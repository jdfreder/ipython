var IPython = {};

var widget_manager = {

    widget_model_types: {},
    widget_view_types: {},
    _handling_sync: false,
    _model_instances: {},
    _controller_sets: {},

    register_widget_model: function (widget_model_name, widget_model_type) {
        this.widget_model_types[widget_model_name] = widget_model_type;
    },


    register_widget_view: function (widget_view_name, widget_view_type) {
        this.widget_view_types[widget_view_name] = widget_view_type;
    },


    get_model: function (widget_id) {
        var model = this._model_instances[widget_id];
        if (model !== undefined && model.id == widget_id) {
            return model;
        }
        return null;
    },


    get_msg_cell: function (msg_id) {
        return null;
    },


    get_kernel: function () {
        return null;
    },


    on_create_widget: function (callback) {
        this._create_widget_callback = callback;
    },


    _handle_create_widget: function (widget_model) {
        if (this._create_widget_callback) {
            try {
                this._create_widget_callback(widget_model);
            } catch (e) {
                console.log("Exception in WidgetManager callback", e, widget_model);
            }
        }
    },

    // Display a widget.
    display_widget: function (widget_id, target_model, view_name, cell, initial_state, parent_id) {
        
        // Create the widget model.
        var model = this.get_model(widget_id);
        if (model === null && this.widget_model_types[target_model] !== undefined) {
            model = new this.widget_model_types[target_model](this, widget_id);
            this._model_instances[widget_id] = model;
            this._handle_create_widget(model);
        }

        if (model === null) {
            console.log('Model with target type "' + target_model + '"" could not be created.');
        } else {
            model.apply_update(initial_state);
            model.display_view(view_name, parent_id, cell);
        }
    },

    // Register a list of controllers and the state sets associated with
    // their values.
    register_controllers: function(controllers, frames) {
        var controller_set ={controllers: controllers, frames: frames};
        for (var i = 0; i < controllers.length; i++) {
            var controller = controllers[i];
            if (this._controller_sets[controller] === undefined) {
                this._controller_sets[controller] = [];
            }
            this._controller_sets[controller].push(controller_set);
        }
    },

    _handle_sync: function(model) {
        if (!this._handling_sync) {
            this._handling_sync = true;
            if (this._controller_sets[model.id] !== undefined && this._controller_sets[model.id].length > 0) {
                for (var i = 0; i < this._controller_sets[model.id].length; i++) {
                    var controller_set = this._controller_sets[model.id][i];
                    var current_state_index = -1;
                    for (var j=0; j < controller_set.frames.length; j++) {
                        var values_match = true;
                        for (var k=0; k < controller_set.controllers.length; k++) {
                            var controller_id = controller_set.controllers[k];
                            var controller_model = this.get_model(controller_id);
                            if (controller_model !== null) {
                                var controller_value = controller_model.get('value');
                                if (controller_value != controller_set.frames[j].states[controller_id].value) {
                                    values_match = false;
                                    break;
                                }    
                            }
                        }

                        if (values_match) {
                            current_state_index = j;
                            break;
                        }
                    }

                    if (current_state_index>=0) {
                        // APPLY STATES TO ALL WIDGETS
                        for (var key in controller_set.frames[current_state_index].states) {
                            var state = controller_set.frames[current_state_index].states[key];
                            var key_model = this.get_model(key);
                            if (key_model !== null) {
                                key_model.apply_update(state);
                            }
                        }

                        // Apply stdout if possible.
                        if (model.last_modified_view !== undefined && model.last_modified_view !== null) {
                            model.last_modified_view.cell.set_stdout(controller_set.frames[current_state_index].stdout);
                        }
                    }
                }
            }    
            this._handling_sync = false;
        }
    },
};

// Define a custom backbone sync method that looks up saved states.
Backbone.sync = function (method, model, options, error) {
    var result = model._handle_sync(method, options);
    if (options.success) {
      options.success(result);
    }
    widget_manager._handle_sync(model);
}; 

// Define a require-like function that doesn't actually load anything.
var define = function(requirements, callback) {
    callback.apply(this, [widget_manager]);
};