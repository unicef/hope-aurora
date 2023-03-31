(function ($) {
    $(function () {
        $("#set_language").on("change", function () {
            var url = $(this).find("option:selected").data("url");
            var parts = url.split("/");
            parts[1] = $(this).val();
            location.href = parts.join("/");
        }).parent().show();
    });
})($);
