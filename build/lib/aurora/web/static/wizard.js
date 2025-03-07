(function ($) {
    $(function () {
        var buttons = "<input type=\"button\" id=\"wizard-prev\" value=\"<<\"/>" +
            "<div class='px-3 inline-flex' id=\"currentPage\"></div>" +
            "<input type=\"button\" id=\"wizard-next\" value=\">>\"/>";
        $(".submit-row").prepend(buttons);
        var currentPage = 0;
        var maxPages = $('.formset-config').length;
        $("[data-page]").hide();
        $("[data-page=\"0\"]").show();
        var update = function () {
            $("#wizard-prev").prop("disabled", currentPage === 0);
            $("#wizard-next").prop("disabled", currentPage === maxPages);
            $("#currentPage").html((currentPage + 1) + " / " + (maxPages + 1));
        };
        update();
        $("#wizard-next").on("click", function () {
            $("[data-page=\"" + currentPage + "\"]").hide();
            $("[data-page=\"" + ++currentPage + "\"]").show();
            update();
        });
        $("#wizard-prev").on("click", function () {
            $("[data-page=\"" + currentPage + "\"]").hide();
            $("[data-page=\"" + --currentPage + "\"]").show();
            update();
        });
    });
})($);
