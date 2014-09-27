// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

// The MouseManager manages the behavior of the user's mouse on the notebook
// document.  This includes cell dragging.
define(['jquery'], function($) {
    "use strict";

    var MouseManager = function(options) {
        // Public constructor.
        this.notebook = options.notebook;
        this.events = options.events;

        // Register document body events.
        $('body').on('mouseup', $.proxy(this._body_mouse_up, this));
        $('body').on('mousemove', $.proxy(this._body_mouse_move, this));

        // Register all of the existing cells.
        this._register_cell($('.cell'));

        // Register new cells as they are created.
        var that = this;
        this.events.on('create.Cell', function(e, data) {
            that._register_cell(data.cell.element);
        });
    }

    MouseManager.prototype._register_cell = function($el) {
        // Listen to a cell's events.
        $el.on('mouseover', $.proxy(this._cell_mouse_over, this));
        $el.on('mouseout', $.proxy(this._cell_mouse_out, this));
        $el.on('mousemove', $.proxy(this._cell_mouse_move, this));
        $el.on('mousedown', $.proxy(this._cell_mouse_down, this));
    }

    MouseManager.prototype._cell_mouse_down = function(e) {
        // Handles cell mouse down.
        this.$dragging_cell = $(e.currentTarget);
    }

    MouseManager.prototype._cell_mouse_over = function(e) {
        // Handles cell mouse over.
        if (this.$dragging_cell) {
            this.$target_cell = $(e.currentTarget);
        }
    }

    MouseManager.prototype._cell_mouse_out = function(e) {
        // Handles cell mouse out (when the mouse leaves the cell).
        if (this.$target_cell) {
            this.$target_cell.removeClass('drag-target-bottom');
            this.$target_cell.removeClass('drag-target-top');
            this.$target_cell = undefined;
        }
    }

    MouseManager.prototype._cell_mouse_move = function(e) {
        // Handles cell mouse move.
        if (this.$dragging_cell) {
            // Only target cell if it's not the one being dragged.
            if (e.currentTarget !== this.$dragging_cell[0]) {

                // Calculate how far the cursor is down the cell (y axis).
                var location_y = ((e.pageY - $(e.currentTarget).offset().top) / $(e.currentTarget).outerHeight());
                
                // If the cursor is more than half way, target below the cell.
                // Otherwise, target above the cell.
                if (location_y > 0.5) {
                    this.cell_drop_top = false;
                    this.$target_cell.removeClass('drag-target-top');
                    this.$target_cell.addClass('drag-target-bottom');
                } else {
                    this.cell_drop_top = true;
                    this.$target_cell.removeClass('drag-target-bottom');
                    this.$target_cell.addClass('drag-target-top');
                }
                this.$dragging_cell.addClass('drag-source');
            } else {
                this.$dragging_cell.removeClass('drag-source');
            }
        }
    }

    MouseManager.prototype._body_mouse_move = function(e) {
        // Handles when the mouse is moved anywhere on the document.
        
        // Disable selection while dragging.
        if (this.$dragging_cell) {
            getSelection().empty();
        }
    }

    MouseManager.prototype._body_mouse_up = function(e) {
        // Handles when a mouse button is released.
        if (this.$dragging_cell) {
            if (this.$target_cell) {

                // Calculate the from and to indicies.
                var to_index = IPython.notebook.find_cell_index(this.$target_cell.data('cell'));
                var from_index = IPython.notebook.find_cell_index(this.$dragging_cell.data('cell'));
                if (!this.cell_drop_top) {
                    to_index += 1;
                }
                if (to_index > from_index) {
                    to_index -= 1;
                }

                // Move only if needed.
                if (to_index != from_index) {

                    // Detach the cell to be moved and reattach it to the DOM
                    // in its new location.
                    this.$dragging_cell.detach();
                    if (this.cell_drop_top) {
                        this.$target_cell.before(this.$dragging_cell);
                    } else {
                        this.$target_cell.after(this.$dragging_cell);
                    }

                    // Select the moved cell and tell the notebook changes have 
                    // been made.
                    IPython.notebook.select(to_index);
                    var cell = IPython.notebook.get_selected_cell();
                    IPython.notebook.focus_cell();
                    IPython.notebook.set_dirty();
                }

            }

            this.$dragging_cell.removeClass('drag-source');
            this.$dragging_cell = undefined;
        }
        if (this.$target_cell) {
            this.$target_cell.removeClass('drag-target-bottom');
            this.$target_cell.removeClass('drag-target-top');
            this.$target_cell = undefined;
        }
    }

    return {'MouseManager': MouseManager};
});
