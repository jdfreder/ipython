{%- extends 'html_full.tpl' -%}

{% block scripts %}
    <link href="http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/2.3.2/css/bootstrap.min.css" rel="stylesheet">
    <link href="http:////cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.3/css/base/minified/jquery-ui.min.css" rel="stylesheet">
    
    <script src="http://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.2/jquery.min.js"></script>
    <script src="http://cdnjs.cloudflare.com/ajax/libs/jqueryui/1.10.3/jquery-ui.min.js"></script>
    <script src="http://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/2.3.2/js/bootstrap.min.js"></script>
    <script src="http://cdnjs.cloudflare.com/ajax/libs/underscore.js/1.5.2/underscore-min.js"></script>
    <script src="http://cdnjs.cloudflare.com/ajax/libs/backbone.js/1.1.0/backbone-min.js"></script>

    <script src="https://rawgithub.com/jdfreder/ipython/static-widgets/IPython/nbconvert/templates/static_widgetmanager.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/base.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/bool.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/button.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/container.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/float.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/float_range.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/image.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/int.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/int_range.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/multicontainer.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/selection.js"></script>
    <script src="https://rawgithub.com/jdfreder/ipython/widget-msg/IPython/html/static/notebook/js/widgets/string.js"></script>

    <style>
        pre {
            background: none;
            border: none;
            padding: 5px;
            margin-bottom: 0px;
        }
    </style>

    {{ super() }}
{% endblock scripts %}

{% block input_group scoped %}
    {{ super() }}

    {% if "snapshot" in cell.metadata %}
        <div id="widget-group-{{cell.prompt_number}}">
            <div class="widget-area">
                <div class="prompt">
                </div>
                <div class="widget-subarea">
                </div>
            </div>
        </div>

        <script type="text/javascript">
            var cell = {
                widget_area: $("#widget-group-{{cell.prompt_number}} .widget-area"),
                widget_subarea: $("#widget-group-{{cell.prompt_number}} .widget-area .widget-subarea"),

                // Special method that allows states to udpate the stdout.
                set_stdout: function(stdout) {
                    var $cell = this.widget_area
                        .parent() // widget-group-
                        .parent(); // cell
                    var $stdout_area = $cell
                        .find('.output_wrapper .output .output_area .output_stdout pre');
                    if ($stdout_area.length == 0) {
                        $cell.append($('<div />').addClass("output_wrapper").html(
                            "<div class='output'><div class='output_area'><div class='prompt'></div><div class='box-flex1 output_subarea output_stream output_stdout'><pre></pre></div></div></div>"));
                    }
                    $stdout_area = $cell
                        .find('.output_wrapper .output .output_area .output_stdout pre');
                    $stdout_area.html(stdout);
                }
            };

            var cell_frames = {{cell.metadata.snapshot.frames}};
            {% if 'controllers' in cell.metadata.snapshot: %}
                var cell_controllers = {{cell.metadata.snapshot.controllers}};
            {% else %}
                var cell_controllers = [];
            {% endif %}
            var cell_display = {{cell.metadata.snapshot.display}};
            widget_manager.register_controllers(cell_controllers, cell_frames);

            for (var i = 0; i < cell_display.length; i++) {
                var model_id = cell_display[i][0];
                var initial_state = cell_frames[0].states[model_id];
                widget_manager.display_widget(model_id, cell_display[i][1], cell_display[i][2], cell, initial_state, cell_display[i][3]);
            }
        </script>
    {% endif %}
{% endblock input_group %}
