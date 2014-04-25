# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import print_function

from time import sleep
import operator

from IPython.display import display
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import CInt, Instance, Bool
from IPython.core.getipython import get_ipython

from .widget_container import ContainerWidget
from .widget_int import IntProgressWidget
from .widget_string import HTMLWidget
from .widget import Widget

class ProgressDialog(LoggingConfigurable):
    """Widget based dialog that is used to display the progess of static widget 
    state computation.

    Show this dialog using the display framework."""

    value = CInt(0, help="Current state index")
    max = CInt(100, help="Number of states")

    def __init__(self, *pargs, **kwargs):
        """Public constructor"""
        LoggingConfigurable.__init__(self, *pargs, **kwargs)

        self._progress_bar = IntProgressWidget(value=0, max=100)
        self._progress_text = HTMLWidget(value='')
        label = HTMLWidget(value='Compiling widgets states...')
        self._dialog = ContainerWidget(children=[label, self._progress_bar, self._progress_text])

        self.on_trait_change(self._update, ['value', 'max'])

    def close(self):
        """Close the dialog."""
        self._dialog.remove_class('in')
        self._dialog.add_class('out')

        sleep(0.5) # Wait for animation to complete.

        self._dialog.close()

    def _update(self, name, old, new):
        """Update the child widgets to reflect the new state."""
        self._progress_bar.value = self.value
        self._progress_bar.max = self.max
        self._progress_text.value ='{0} of {1}'.format(self.value, self.max)

    def _ipython_display_(self, **kwargs):
        """Called when `IPython.display.display` is called on this instance."""
        display(self._dialog)

        self._dialog.add_class('fade in align-center')
        self._progress_bar.add_class('progress-striped active')


class StaticWidgetManager(LoggingConfigurable):
    """Static widget manager.

    Used to calculate and store all possible widget state combinations for later
    use."""

    # backend = Instance('IPython.html.widgets.backend.BackendBase',
    #     help="""Backend instance to use to store the precomputed widget states.""")
    display_calls_only = Bool(False, config=True, help="Only capture widget display calls.")
    capture_all = Bool(False, config=True, help="Capture all of the widgets regardless of their static flag.")
    
    shell = Instance('IPython.core.interactiveshell.InteractiveShellABC')
    def _shell_default(self):
        return get_ipython()

    def __init__(self, backend, **kwargs):
        """Public constructor."""
        LoggingConfigurable.__init__(self, **kwargs)
        self.backend = backend

        self._disposed = False
        self._executing = False
        self._captured_widgets = []
        self._state_stack = []

        self.shell.events.register('pre_run_cell', self._handle_preexecute)
        self.shell.events.register('post_run_cell', self._handle_postexecute)

    def __del__(self):
        """If the GC gets this before the user calls dispose, call dispose for
        the user."""
        self.dispose()

    def dispose(self):
        """Remove the registered event hooks."""
        if not self._disposed:
            self._disposed = True
            self.shell.events.unregister('pre_run_cell', self._handle_preexecute)
            self.shell.events.unregister('post_run_cell', self._handle_postexecute)

    def _handle_preexecute(self):
        """Gets called before any cell is executed."""
        self._executing = True
        self._captured_widgets = []
        Widget.on_widget_constructed(self._handle_widget_construction)

    def _handle_postexecute(self):
        """Gets called after any cell is executed."""
        Widget.on_widget_constructed(None)
        self._executing = False
        self.backend.commit_execution_msgs()

        widgets = self._captured_widgets
        if not self.display_calls_only and len(widgets) > 0:
            # Push the current widgets state
            self._push_widget_states()

            # Create a progress dialog.
            dialog = ProgressDialog()
            dialog.value = 0
            dialog.max = reduce(operator.mul, [w.get_state_count() for w in widgets])

            # Emulate all of the possible widget states and capture the widget 
            # outputs.
            def capture():
                self.backend.commit_state_msgs(self._get_state())
                dialog.value += 1
            callbacks = [lambda i=i: widgets[i].run_states(callbacks[i + 1]) for i in range(len(widgets))] + [capture]
            callbacks[0]()
            
            # Close the dialog.
            dialog.close()

            # Pop the current widgets state
            self._pop_widget_states()

    def _handle_send(self, widget, msg):
        """Capture a send event from a widget."""
        if self._executing:
            self.backend.append_execution_msg(msg)
        else:
            self.backend.append_state_msg(msg)
        return True # Allow the msg to be sent.

    def _handle_widget_construction(self, widget, static=False, **kwargs):
        """Gets called when a widget is constructed."""
        # Start capturing the widget's comm messages.
        if static or self.capture_all:
            self._captured_widgets.append(widget)
            widget.comm_send_callback = self._handle_send

    def _get_state(self):
        return {w: w.get_state() for w in self._captured_widgets}

    def _push_widget_states(self):
        self._state_stack.append(self._get_state())

    def _pop_widget_states(self):
        if len(self._state_stack) > 0:
            states = self._state_stack.pop()
            for widget, state in states.items():
                widget.set_state(state)
        
