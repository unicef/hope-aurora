(function ($) {
    $(document).ready(function () {

        var $me = $("#form_editor_script");
        var refreshUrl = $me.data("url");
        var $iFrame1 = $('#widget_display');
        var $iFrame2 = $('#widget_code');
        var $iFrame3 = $('#widget_attrs');

        var $radioRender = $("#radio_display");
        var $radioCode = $('#radio_code');
        var $radioAttributes = $('#radio_attrs');

        $(".toolbutton").on("click", function () {
            const action = $(this).data('action');
            const op = $(this).data('op');
            const fieldId = $(this).parents('div.cm-container').data('fieldid');
            const editor = $(`#${fieldId}`).data('CodeMirror');
            if (action) {
                window.cmToolBar.action(editor, action);
            } else if (op) {
                window.cmToolBar[op](editor);
            }
        });

        function update() {
            var formData = $("form").serialize();
            $(".field-error").remove();
            $.post(refreshUrl, formData)
                .done(function (data) {
                    $iFrame1[0].contentWindow.location = $iFrame1[0].contentWindow.location.href;
                    $iFrame2[0].contentWindow.location = $iFrame2[0].contentWindow.location.href;
                    $iFrame3[0].contentWindow.location = $iFrame3[0].contentWindow.location.href;
                })
                .fail(function (xhr) {
                    var errors = xhr.responseJSON;
                    var fieldErrors = errors.field;
                    var kwargsErrors = errors.kwargs;
                    var widget_kwargs = errors.widget_kwargs;
                    var smart = errors.smart;
                    for (const property in fieldErrors) {
                        $(`#id_field-${property}`).before(`<div class="field-error">${fieldErrors[property]}</div>`);
                    }
                })
        }

        $('input[type=checkbox],input[type=radio]').on('click', function () {
            update();
        });
        $('select').on('change', function () {
            update();
        });
        $('input,textarea').on('keyup', function () {
            clearTimeout($.data(this, 'timer'));
            var wait = setTimeout(update, 500);
            $(this).data('timer', wait);
        });
        $('textarea.js-editor').each(function (i, e) {
            var editor = $(e).data("CodeMirror");
            if (editor) {
                editor.refresh();
                editor.on('change', function () {
                    editor.save()
                })
            }
        });
        $("#event_selector").on("change", function (){
            let sel = $(this).val();
            $('#events .code').removeClass('selected');
            $(`#event_${sel}`).addClass('selected').find('textarea.js-editor').each(function (i, e) {
                var editor = $(e).data("CodeMirror");
                if (editor) editor.refresh();
            });
        });
        $("#radio_display, #radio_code, #radio_attrs").on("click", function () {
            $radioRender.is(":checked") ? $iFrame1.show() : $iFrame1.hide();
            $radioCode.is(":checked") ? $iFrame2.show() : $iFrame2.hide();
            $radioAttributes.is(":checked") ? $iFrame3.show() : $iFrame3.hide();
        })
        $(".tabs th").on("click", function () {
            const targetName = $(this).data('target');
            $('.tabs th').removeClass('selected');
            $('.cfg-form').addClass('collapsed');
            $(this).addClass('selected');
            $(`#${targetName}`).toggleClass('collapsed');
            $('textarea.js-editor').each(function (i, e) {
                var editor = $(e).data("CodeMirror");
                editor.refresh();
            });
        });
        $radioRender.trigger("click");
    })
})(django.jQuery);
