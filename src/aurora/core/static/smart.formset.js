var configureFormsets = function (configs) {
    configs.forEach(function (c, i) {
        var config = {};
        $.extend(true, config, DEFAULT, c);
        var $target = $("." + config.formCssClass);
        if (!$target){
            throw Error(configs)
        }
        config.initialized = function ($$) {
            if ($$.options.showCounter) {
                updateCounter($$, null);
            }
            var $btn = $$.parent().find('div.formset-add-row a');
            if ($btn.is(":visible")) {
                $btn.parent().attr('data-msgid', config.original.addText)
            }
        };
        $target.formset(config);
    });
};
var updateCounter = function ($$, $row) {
    if ($$.options.showCounter) {
        var $fs = $$.parents(".formset");
        var forms = $fs.find(".form-container").length;
        $fs.find(".fs-counter").each(function (i, e) {
            var idx = 1 + i;
            var alink = "<a class='aname' id=\"" + $$.options.prefix + "_member_" + idx + "\"></a>";
            var pages = $$.options.counterPrefix + ": " + idx + "/" + forms;
            var next = "<span class='disabled next'></span>";
            var prev = "<span class='disabled prev'></span>";
            var remove = "<a class=\"" + $$.options.deleteCssClass + "\" href=\"javascript:void(0)\"><span class='remove'></span></a>";

            if (idx > 1) {
                prev = "<a class='prev' href=\"#" + $$.options.prefix + "_member_" + (idx - 1) + "\"></a>";
            }
            if (idx < forms) {
                next = "<a class='next' href=\"#" + $$.options.prefix + "_member_" + (idx + 1) + "\"></a>";
            }
            alink += '<div class="pages mt-1">' + pages + '</div>';
            alink += '<div class="nav mt-1">' + prev + next + '</div>'
            // alink += '<div class="nav mt-1">' + remove + '</div>'

            $(e).html(alink);
        });
    }
};
var DEFAULT = {
    // addText: "add another",
    // deleteText: "remove",
    initialized: null,
    removed: function ($$, row) {
        updateCounter($$, null);
    },
    added: function ($$, row) {
        // var $fs = $(row).parents('.forms')
        var highlight = "border-gray-900 border-2 bg-gray-200";
        $(row).addClass(highlight);
        updateCounter($$, null);
        setTimeout(function () {
            $(row).removeClass(highlight);
        }, 400);

        if ($$.options.onAdd && window[$$.options.onAdd]) {
            window[$$.options.onAdd]($$, row);
        }
        $(row).find(".vDateField").each(function (i) {
        });
        $(row).find(".vPictureField").each(function (i, obj) {
            initWebCamField(obj);
        });

        $(row).find(".question-visibility").each(function (i, e) {
            $(e).on("click", function () {
                smart.handleQuestion(this);
            });
        });
    }
};

(function ($) {
    $(function () {
        var formsetConfig = [];
        $(".formset-config script[type=\"application/json\"]").each(function (i, e) {
            var $e = $(e);
            var value = JSON.parse($e.text());
            formsetConfig.push(value);
        });
        if (formsetConfig.length > 0) {
            configureFormsets(formsetConfig);
        }
        $("input:checked[onchange]").trigger("change");
    });
})($);
