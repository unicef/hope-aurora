(function ($) {
    $(function () {
        var currentPage = 0;
        $("[data-page]").hide();
        $("[data-page=\"0\"]").show();
        var update = function () {
            $("#wizard-prev").prop("disabled", currentPage === 0);
            $("#wizard-next").prop("disabled", currentPage === maxPages);
            $("#currentPage").html((currentPage+1) + " / " + (maxPages +1));
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

        if (formsetConfig.length > 0) {
            configureFormsets(formsetConfig);
        }
        $("input:checked[onchange]").trigger("change");
        $("#spinner").hide();
    });
})($);
