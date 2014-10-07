// Copyright (c) IPython Development Team.
// Distributed under the terms of the Modified BSD License.

define([
    "jquery",
    "widgets/js/widget",
    "notebook/js/outputarea",
    "bootstrap"
], function($, widget, outputarea){

    var OutputView = widget.DOMWidgetView.extend({
        render: function() {
            // Call the base.
            OutputView.__super__.render.apply(this, [arguments]);

            this.output_area = new outputarea.OutputArea({
                selector: this.$el, 
                prompt_area: true, 
                events: this.widget_manager.notebook.events, 
                keyboard_manager: this.widget_manager.keyboard_manager});
        },
    });

    return {
        'OutputView': OutputView,
    };
});
