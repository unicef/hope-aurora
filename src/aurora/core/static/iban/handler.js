;(function ($) {
    $(function () {

        var validateIban = function (o) {
            var f = new aurora.Field(o);
            var v = f.getValue();
            if (v) {
                if (!IBAN.isValid(v)) {
                    f.setError("Invalid IBAN");
                    return false;
                } else {
                    f.setError("");
                    return true;
                }
            }
        };

        $("input.IbanWidget").each(function () {
            $(this).data("validator", validateIban);
        }).on("keyup", function () {
            if (IBAN.isValid($(this).val())) {
                $(this).addClass("bg-green-200").removeClass("bg-red-200");
            } else {
                $(this).addClass("bg-red-200").removeClass("bg-green-200");
            }
        })

    });
})(jQuery || django.jQuery);
