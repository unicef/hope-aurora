(function ($) {
    function delay(callback, ms) {
        var timer = 0;
        return function () {
            var context = this, args = arguments;
            clearTimeout(timer);
            timer = setTimeout(function () {
                callback.apply(context, args);
            }, ms || 0);
        };
    }

    $.fn.tableFilter = function (t) {
        var $table = t;
        this.on("keyup", delay(function (e) {
            console.log(this.value)
            let filter = this.value.toUpperCase();
            $table.find('tbody tr').each(function (i, el) {
                let txt = $(el).find("td,caption").text();
                if (txt.toUpperCase().indexOf(filter) > -1) {
                    $(el).closest(".section").show();
                    $(el).show();
                } else {
                    $(el).hide();
                }
                $("table.section").each(function (i, t) {
                    if ($(t).find("tr:visible").length === 0) {
                        $(t).hide();
                    }
                });
            });
        }, 300)).trigger("keyup").focus();
    };
})(django.jQuery);
