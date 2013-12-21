"""StaticWidgetManager class.  Use to enable widget output in nbconvert.  Allows
the user to pre-compute all bounded widget inputs and resultant widget + stdout 
+ custommsg states.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import sys
import json
import copy

import IPython
from IPython.html import widgets
from IPython.utils.capture import capture_output
from IPyhton.core.prefilter import PrefilterChecker

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class CellExecutionEvents(PrefilterChecker):

    def __init__(self, ipython):
        PrefilterChecker.__init__(self, shell=ipython.prefilter_manager.shell, 
            prefilter_manager=ipython.prefilter_manager, 
            parent=ipython.prefilter_manager)
        self.is_running = False
        self._ipython = ipython
        self._ipython.register_post_execute(self._handle_cell_stop)
        self.is_disposed = False
        self._start_callback = None
        self._stop_callback = None
        
    def __del__(self):
        self.dispose()
        
    def dispose(self):
        if not self.is_disposed:
            del _ipython._post_execute[self._handle_cell_stop]
            self.is_disposed = True
            self._handle_cell_stop()
            self.prefilter_manager.unregister_checker(self)

    def check(self, line_info):
        """Called when a line is executed in a cell."""
        if not self._is_running:
            self.is_running = True
            if self._start_callback is not None and callable(self._start_callback):
                self._start_callback()

    def _handle_cell_stop(self):
        if self._is_running:
            self.is_running = False
            if self._stop_callback is not None and callable(self._stop_callback):
                self._stop_callback()

    def on_start(self, callback):
        self._start_callback = callback

    def on_stop(self, callback):
        self._stop_callback = callback


class StaticWidgetManager(object):
    
    def __init__(self):
        self._sent_messages = {}
        self._cell_events = CellExecutionEvents(get_ipython())
        self._cell_events.on_start(self._handle_cell_start)
        self._cell_events.on_stop(self._handle_cell_stop)

        Widget.on_widget_constructed(self._handle_widget_constructed)
        self.is_disposed = False
        
    def __del__(self):
        self.dispose()
        
    def dispose(self):
        if not self.is_disposed:
            Widget.on_widget_constructed(None)
            self._cell_events.dispose()
            self.is_disposed = True

    def _handle_widget_constructed(self, widget):
        pass

    def _handle_cell_start(self):
        pass

    def _handle_cell_stop(self):
        pass

    def capture(self):
        if self.is_disposed:
            raise Exception('Object disposed')
            
        capture_widgets = []
        original_values = {}
        capture_values = {}
        for call in widgets.Widget.display_calls:
            widget = call[0]
            if not widget in capture_widgets:
                capture_widgets.append(widget)
                self._hook_send(widget)
                
                # Try to get the bounded values for the widget.
                bounded_values = self._get_bounded_values(widget, call[1])
                if bounded_values is not None:
                    capture_values[widget] = bounded_values
                    original_values[widget] = widget.value
            
        if len(capture_widgets) > 0:
            with capture_output() as io:
                self._captured_io = io

                original_clear_output = self._ipython.display_pub.clear_output
                def handle_clear_output(wait=False):
                    self._captured_io._stdout.truncate(0)
                    self._captured_io._stderr.truncate(0)
                    self._captured_io._stdout.seek(0)
                    self._captured_io._stderr.seek(0)
                    original_clear_output(wait=wait)
                self._ipython.display_pub.clear_output = handle_clear_output
                
                # Build the static display call list.
                static_display_calls = []
                for call in widgets.Widget.display_calls:
                    display_call = []
                    display_call.append(hex(id(call[0]))) # unique id
                    display_call.append(call[0].target_name) # model name
                    display_call.append(call[1]) # view name
                    if len(call) > 2:
                        display_call.append(hex(id(call[2]))) # parent
                    static_display_calls.append(display_call)
                
                results = {}
                results['display'] = json.dumps(static_display_calls)

                if len(capture_values) > 0:
                    # Save the id's of the widget models that need to be monitored
                    results['controllers'] = []
                    for input_widget in capture_values.keys():
                        results['controllers'].append(hex(id(input_widget))) 
                        
                    results['frames'] = json.dumps(self._each_value(capture_values, capture_widgets))
                else:
                    this_widget_capture = {}
                    for capture_widget in capture_widgets:
                        this_widget_capture[hex(id(capture_widget))] = self._get_state(capture_widget)
                    results['frames'] = json.dumps([{'states': this_widget_capture}])

                capture_widgets[0].set_snapshot(results)
                
                self._ipython.display_pub.clear_output = original_clear_output
                del self._captured_io

            # Revert widgets back to their initial values
            for (widget, value) in original_values.items():
                widget.value = value


    def _get_bounded_values(self, widget, view_name):
        if isinstance(widget, widgets.IntRangeWidget) and \
        (view_name == "IntSliderView" or view_name == "IntTextView"):
            return range(widget.min, widget.max + widget.step, widget.step)
        elif isinstance(widget, widgets.FloatRangeWidget) and \
        (view_name == "FloatSliderView" or view_name == "FloatTextView"):
            return [x * widget.step + widget.min for x in range(0, int((widget.max - widget.min) / widget.step))]
        elif isinstance(widget, widgets.SelectionWidget):
            return widget.values
        elif isinstance(widget, widgets.BoolWidget):
            return [True, False]
        else:
            return None
    

    def _each_value(self, widget_values, capture_widgets):
        (widget, values) = widget_values.popitem()
        results = []
        for value in values:
            
            widget.value = value
            
            if len(widget_values) > 0:
                copied_widget_values = dict(widget_values)
                results.extend(self._each_value(copied_widget_values, capture_widgets))
            else:
                
                this_widget_capture = {}
                for capture_widget in capture_widgets:
                    this_widget_capture[hex(id(capture_widget))] = self._get_state(capture_widget)
                
                capture = {}
                capture['states'] = this_widget_capture
                capture['sends'] = self._sent_messages
                self._sent_messages = {}
                capture['stdout'] = self._captured_io.stdout
                capture['stderr'] = self._captured_io.stderr
                
                results.append(capture)
        return results
    

    def _hook_send(self, widget):
        original_send = widget.send
        def handle_send(msg):
            original_send(msg)
            if not hex(id(widget)) in sent_messages:
                self._sent_messages[hex(id(widget))] = []
            self._sent_messages[hex(id(widget))].append(msg)
        widget.send = handle_send

        
    def _get_state(self, widget):
        state = {}
        for name in widget.keys:
            state[name] = copy.deepcopy(getattr(widget, name))
        return state
    
    
    def _handle_cell_executed(self):
        widgets.Widget.display_calls = []

static_widgetmanager = StaticWidgetManager()
