"""Button class.  

Represents a button in the frontend using a widget.  Allows user to listen for
click events on the button and trigger backend code when the clicks are fired.
"""

# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.

# Imports
from .widget import DOMWidget
from IPython.utils.traitlets import Unicode

# Classes
class Output(DOMWidget):
    """Output widget.

    Used to display output (stdout, stderr, display, etc...)."""
    _view_name = Unicode('OutputView', sync=True)
