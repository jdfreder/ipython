// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

/**
 * ActiveCellQuerier class.
 * @module IPython
 * @namespace IPython
 * @submodule ActiveCellQuerier
 */

(function () {
    "use strict";

    // Use require.js 'define' method so that require.js is intelligent enough to
    // syncronously load everything within this file when it is being 'required' 
    // elsewhere.
    define([], function () {

        var ActiveCellQuerier = function (notebook) {
            // Public constructor
            // Listen for the ActiveCellQuerier comm.
            this._notebook = notebook;
            notebook.kernel.comm_manager.register_target('ActiveCellQuerier', $.proxy(this._handle_comm_open, this));
        };

        ActiveCellQuerier.prototype._handle_comm_open = function (comm, msg) {
            // Handle when a comm is opened.
            this.comm = comm;
            comm.on_close($.proxy(this._handle_comm_closed, this));
            comm.on_msg($.proxy(this._handle_comm_msg, this));
        };

        ActiveCellQuerier.prototype.close = function () {
            // Close the internal comm.
            this.comm.close();
            delete this.comm;
        };

        ActiveCellQuerier.prototype._handle_comm_closed = function (msg) {
            // Handle when the comm is closed.
            delete this.comm;
        };

        ActiveCellQuerier.prototype._handle_comm_msg = function (msg) {
            // Handle when a comm msg is received.
            if (msg.content.data === 'id?') {
                // In the notebook, the index of a cell can be, and is here, 
                // used as a unique id for that cell.
                var cell = this._notebook.get_msg_cell(msg.parent_header.msg_id);
                var index = null;
                if (cell) {
                    index = this._notebook.find_cell_index(cell);
                }
                this.comm.send(index || -1); // where -1 means undefined
            }
        };

        IPython.ActiveCellQuerier = ActiveCellQuerier;
        return IPython.ActiveCellQuerier;
    });
}());
