from time import sleep

from IPython.display import display
from IPython.config import LoggingConfigurable
from IPython.utils.traitlets import CInt

from .widget_container import ContainerWidget
from .widget_int import IntProgressWidget
from .widget_string import HTMLWidget

class ProgressDialog(LoggingConfigurable):
    """Widget based dialog that is used to display the progess of static widget 
    state computation.

    Show this dialog using the display framework."""

    value = CInt(0, help="Current state index")
    max = CInt(100, help="Number of states")

    def __init__(self, *pargs, **kwargs):
        """Public constructor"""
        LoggingConfigurable.__init__(self, *pargs, **kwargs)

        self._progress_bar = IntProgressWidget(value=50, max=100)
        self._progress_text = HTMLWidget(value='0 of N/A')
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

