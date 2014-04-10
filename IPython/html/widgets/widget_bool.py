"""BoolWidget class.  

Represents a boolean using a widget.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, Bool

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _BoolWidget(DOMWidget):
    value = Bool(False, help="Bool value", sync=True)
    description = Unicode('', help="Description of the boolean (label).", sync=True) 
    disabled = Bool(False, help="Enable or disable user changes.", sync=True)

    def get_state_count(self):
        """Get the number of states that this widget can be in.

        This is used when one needs to know how many iterations run_states will
        make."""
        return 2
    
    def run_states(self, callback):
        """Iterate through each possible state of this widget.

        Parameters
        ----------
        callback: callable
            Callback to call for each state."""
        original_value = self.value
        self.value = True
        callback()
        self.value = False
        callback()
        self.value = original_value


class CheckboxWidget(_BoolWidget):
    _view_name = Unicode('CheckboxView', sync=True)


class ToggleButtonWidget(_BoolWidget):
    _view_name = Unicode('ToggleButtonView', sync=True)
    
