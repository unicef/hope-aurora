(function ($) {
    $(function () {
        var validators = [];

        $("input[data-smart-validator]").each(function (i, e) {
            const funcName = $(this).data("smart-validator");
            const $field = $(e);
            if ( validators.indexOf(funcName) <0){
                $.getScript("/api/validator/" + funcName + "/validator/", function (data, textStatus, jqxhr) {
                    validators[funcName] = window[funcName];
                    console.log("Found validator '" + funcName+ "' for Field", $field.attr("name"));

                    $field.on("blur", function () {
                        $field.parent().find("span.errors").find("ul.errorlist").remove();
                        const ret = validators[funcName]($(this).val());
                        if (typeof ret === "string") {
                            $field.parent().find("span.errors").html("<ul class='errorlist'><li>" + gettext(ret) + "</li></ul>");
                        }
                    });
                });
            }
        });

        $(".formset[data-smart-validator]").each(function (i, e) {
            console.log("Found validator for FormSet:", e);
        });

        $("form[data-smart-validator]").each(function (i, e) {
            console.log("Found validator for Field:", $(e).attr("id"));

        });

        $(".module[data-smart-validator]").each(function (i, e) {
            console.log("Found validator for Module:", e);

        });

    });
})($);
