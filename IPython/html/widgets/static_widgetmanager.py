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
        def _handle_display(**kwargs):
            self._handle_widget_displayed(widget, **kwargs)
        widget.on_displayed(**kwargs)

    def _handle_widget_displayed(self, widget, **kwargs):
        if kwargs.get('capture', False):
            if widget not in self._capture_widgets:
                self._capture_widgets.append(widget)
                self._hook_send(widget)
                
                # Try to get the bounded values for the widget.
                bounded_values = self._get_bounded_values(widget, call[1])
                if bounded_values is not None:
                    self.capture_values[widget] = bounded_values
                    self.original_values[widget] = widget.value

    def _handle_cell_start(self):
        self.capture_widgets = [] # Widgets that are being captured statically.
        self.original_values = {} # Original `value`s of the captured widget(s).
        self.capture_values = {} # Dictionary of widget ids and lists of valid values to use.
        self.sent_msgs = [] # List of captured widget messages.  Chronologically ordered.

    def _handle_cell_stop(self):
        if len(self.capture_widgets) > 0:
            # Read current messages, save.
            initial_messages = self.sent_msgs
            self.sent_msgs = []

            # Hook output.
            frames = []
            with capture_output() as io:
                self._captured_io = io
                # Hook clear output.
                original_clear_output = self._ipython.display_pub.clear_output
                def handle_clear_output(wait=False):
                    self._captured_io._stdout.truncate(0)
                    self._captured_io._stderr.truncate(0)
                    self._captured_io._stdout.seek(0)
                    self._captured_io._stderr.seek(0)
                    original_clear_output(wait=wait)
                self._ipython.display_pub.clear_output = handle_clear_output

                # Brute force all combinations.
                frames = self._each_value(self.capture_values)

                # Restore clear output
                self._ipython.display_pub.clear_output = original_clear_output
                del self._captured_io

            # Clean-up.  Remove hooks.
            for widget in self.capture_widgets:
                self._unhook_send(widget)

            # Commit the capture results to the notebook.
            results = {
                'initial': initial_messages
                'frames': frames
            }
            self.capture_widgets[0].set_widget_cache(json.dumps(results))

    def _each_value(self, widget_values, set_values=None):
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
                
                capture['sends'] = self.sent_msgs
                self.sent_msgs = []
                capture['stdout'] = self._captured_io.stdout
                capture['stderr'] = self._captured_io.stderr
                
                results.append(capture)
        return results
    

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
    

    def _hook_send(self, widget):
        widget.original_send = widget._send
        def handle_send(msg):
            widget.original_send(msg)
            self.sent_msgs.append((hex(id(widget)), msg)
        widget._send = handle_send

    def _unhook_send(self, widget):
        widget._send = widget.original_send
        

static_widgetmanager = StaticWidgetManager()
