"""FloatWidget class.  

Represents an unbounded float using a widget.
"""
# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
import math
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode, CFloat, Bool, Enum

#-----------------------------------------------------------------------------
# Classes
#-----------------------------------------------------------------------------
class _FloatWidget(DOMWidget):
    value = CFloat(0.0, help="Float value", sync=True) 
    disabled = Bool(False, help="Enable or disable user changes", sync=True)
    description = Unicode(help="Description of the value this widget represents", sync=True)


class _BoundedFloatWidget(_FloatWidget):
    max = CFloat(100.0, help="Max value", sync=True)
    min = CFloat(0.0, help="Min value", sync=True)
    step = CFloat(0.1, help="Minimum step that the value can take (ignored by some views)", sync=True)

    def __init__(self, *pargs, **kwargs):
        """Constructor"""
        DOMWidget.__init__(self, *pargs, **kwargs)
        self.on_trait_change(self._validate, ['value', 'min', 'max'])

    def get_state_count(self):
        """Get the number of states that this widget can be in.

        This is used when one needs to know how many iterations run_states will
        make."""
        return int(math.floor((self.max - self.min) / self.step))
    
    def run_states(self, callback):
        """Iterate through each possible state of this widget.

        Parameters
        ----------
        callback: callable
            Callback to call for each state."""
        original_value = self.value
        count = self.get_state_count()
        for i in range(count):
            self.value = self.min + i * self.step
            callback()
        self.value = original_value

    def _validate(self, name, old, new):
        """Validate value, max, min."""
        if self.min > new or new > self.max:
            self.value = min(max(new, self.min), self.max)


class FloatTextWidget(_FloatWidget):
    _view_name = Unicode('FloatTextView', sync=True)


class BoundedFloatTextWidget(_BoundedFloatWidget):
    _view_name = Unicode('FloatTextView', sync=True)


class FloatSliderWidget(_BoundedFloatWidget):
    _view_name = Unicode('FloatSliderView', sync=True)
    orientation = Enum([u'horizontal', u'vertical'], u'horizontal', 
        help="Vertical or horizontal.", sync=True)
    readout = Bool(True, help="Display the current value of the slider next to it.", sync=True)


class FloatProgressWidget(_BoundedFloatWidget):
    _view_name = Unicode('ProgressView', sync=True)
