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


#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class StaticWidgetManager(object):
    
    def __init__(self):
        self._sent_messages = {}
        self._ipython = get_ipython()
        self._ipython.register_post_execute(self._handle_cell_executed)
        self.is_disposed = False
        
    def __del__(self):
        self.dispose()
        
    def dispose(self):
        if not self.is_disposed:
            del _ipython._post_execute[self._handle_cell_executed]
            self.is_disposed = True

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
                
                if isinstance(widget, widgets.IntRangeWidget) and \
                (call[1] == "IntSliderView" or call[1] == "IntTextView"):
                    capture_values[widget] = range(widget.min, widget.max + widget.step, widget.step)
                    original_values[widget] = widget.value
                elif isinstance(widget, widgets.FloatRangeWidget) and \
                (call[1] == "FloatSliderView" or call[1] == "FloatTextView"):
                    capture_values[widget] = [x * widget.step + widget.min for x in range(0, int((widget.max - widget.min) / widget.step))]
                    original_values[widget] = widget.value
                elif isinstance(widget, widgets.SelectionWidget):
                    capture_values[widget] = widget.values
                    original_values[widget] = widget.value
                elif isinstance(widget, widgets.BoolWidget):
                    capture_values[widget] = [True, False]
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
