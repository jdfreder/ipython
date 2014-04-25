# Copyright (c) IPython Development Team.
# Distributed under the terms of the Modified BSD License.
from __future__ import print_function

from copy import copy

from IPython.kernel.comm import Comm

class BackendBase():
    """Base class used to define a storage backend for a static widget manager."""
    
    def __init__(self):
        """Public constructor"""
        self.execution_msgs = []
        self.state_msgs = []

    def append_execution_msg(self, msg):
        """Append a widget display msg to the cache."""
        self.execution_msgs.append(msg)
    
    def commit_execution_msgs(self):
        """Commits the display msgs to the storage."""
        self.execution_msgs = []
        # Implementors should handle association to cells themselves.
    
    def append_state_msg(self, msg):
        """Append a widget display msg to the cache."""
        self.state_msgs.append(msg)
    
    def commit_state_msgs(self, state):
        """Commits the state and its msgs to the storage."""
        self.state_msgs = []
        # Implementors should handle association of states/cells themselves.


class ActiveCellQuerier():
    """Used to query the active cell index."""

    def __init__(self):
        """Public constructor"""
        self._closed = False
        self._comm = Comm(target_name='ActiveCellQuerier')
        self._comm.on_msg(self._handle_msg)
        self._comm.on_close(self.close)
        self._callbacks = []

    def __del__(self):
        """If the GC gets this before the user calls close, call close for
        the user."""
        self.close()

    def close(self):
        """Close this cell querier and any connections it may have with the 
        front-end."""
        if not self._closed:
            self._comm.close()
            self._closed = True

    def get_index(self, callback):
        if self._closed:
            raise ValueError('This ActiveCellQuerier has been closed.')
        if not callable(callback):
            raise ValueError('callback must be callable')
        self._callbacks.append(callback)
        self._comm.send('id?')
    
    def _handle_msg(self, msg):
        """Called when a msg is received from the front-end"""
        [c(int(msg['content']['data'])) for c in self._callbacks]
        del self._callbacks[:]


class NotebookLogBackend(BackendBase):
    """Base class used to define a storage backend for a static widget manager."""
    
    def __init__(self):
        BackendBase.__init__(self)
        self.log = ''
        self._active_cell_querier = ActiveCellQuerier()

    def commit_execution_msgs(self):
        """Commits the display msgs to the storage."""
        def process_msgs(cell_index, msgs=copy(self.execution_msgs)):
            self._log('{0} executing msgs captured for cell #{1}'.format(len(msgs), cell_index))
        self._active_cell_querier.get_index(process_msgs)
        BackendBase.commit_execution_msgs(self)
    
    def commit_state_msgs(self, state):
        """Commits the state and its msgs to the storage."""
        def process_msgs(cell_index, widget_states=state, msgs=copy(self.state_msgs)):
            self._log('{0} state msgs captured for cell #{1}'.format(len(msgs), cell_index))
        self._active_cell_querier.get_index(process_msgs)
        BackendBase.commit_state_msgs(self, state)

    def _log(self, text):
        self.log += text + '\n'
        print(text)

