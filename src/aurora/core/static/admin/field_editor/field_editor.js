(function ($) {
    var $me = $("#field_editor_script");
    var refreshUrl = $me.data("url");
    var $iFrame1 = $('#widget_display');
    var $iFrame2 = $('#widget_code');
    var $iFrame3 = $('#widget_attrs');

    var $radioRender = $("#radio_display");
    var $radioCode = $('#radio_code');
    var $radioAttributes = $('#radio_attrs');

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
                console.log(1111, errors)
                var fieldErrors = errors.field;
                var kwargsErrors = errors.kwargs;
                var widget_kwargs = errors.widget_kwargs;
                var smart = errors.smart;
                for (const property in fieldErrors) {
                    $(`#id_field-${property}`).before(`<div class="field-error">${fieldErrors[property]}</div>`);
                }
                // for (const property in kwargsErrors) {
                //     console.log(`${property}: ${kwargsErrors[property]}`);
                // }
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

    $("#radio_display, #radio_code, #radio_attrs").on("click", function () {
        $radioRender.is(":checked") ? $iFrame1.show() : $iFrame1.hide();
        $radioCode.is(":checked") ? $iFrame2.show() : $iFrame2.hide();
        $radioAttributes.is(":checked") ? $iFrame3.show() : $iFrame3.hide();
    })


})(django.jQuery);
