const i18n = {
    displayIcons: function (resp) {
        const msgIfMissing = "[Err: missing 'data-msgid']";
        $("<script type=“text/template” id=\"i18n-template\">\n" +
            "        <span class=\"inline-flex staff-i18n staff-i18n staff-tooltip align-left \">\n" +
            "            <span class=\"tooltiptext\">\n" +
            "                <p><span class=\"label\">Lang</span>{{LANGUAGE_CODE}}</p>\n" +
            "                <p><span class=\"label\">Message</span>{{ORIGINAL}}</p>\n" +
            "            </span>\n" +
            "            <label aria-label=\"Edit\">\n" +
            "                <a target=\"_edit\" class=\"i18n\"\n" +
            "                   data-url=\"" + resp.editUrl + "\"" +
            "                   data-lang=\"" + resp.languageCode + "\"" +
            "                   data-original=\"{{ORIGINAL}}\"" +
            "                   data-encoded=\"{{ENCODED}}\"" +
            "                   href=\"#\"></a>\n" +
            "            </label>\n" +
            "        </span>\n" +
            "    </script>").appendTo("body");

        $("[data-msgid]").each(function (i, e) {
            var original = $(e).data("msgid");
            if (original) {
                var $tooltip;
                var html = $("#i18n-template").html()
                                              .replaceAll("{{ORIGINAL}}", original)
                                              .replaceAll("{{ENCODED}}", encodeURIComponent(original))
                                              .replaceAll("{{LANGUAGE_CODE}}", LANGUAGE_CODE);

                if ($(e).hasClass("itrans-before") || $(e).is("input")) {
                    $tooltip = $(e).before(html);
                } else {
                    $tooltip = $(e).prepend(html);
                }
                $.each($(e).data(), function (key, value) {
                    if (key.startsWith("i18n")) {
                        var label = key.replace("i18n", "");
                        $tooltip.find(".tooltiptext")
                                .append("<p><span class=\"label\">" + label + "</span>" + value + "</p>");
                    }
                });
            }
        });

        $("a.i18n").on("click", function (e) {
            var url = $(this).data("url");
            e.preventDefault();
            if ($(this).data("original") !== msgIfMissing) {
                $("<form target=\"_edit\" action=\"" + url + "\" method=\"post\">" +
                    "<input type=\"hidden\" name=\"lang\" value=\"" + $(this).data("lang") + "\">" +
                    "<input type=\"hidden\" name=\"msgid\" value=\"" + $(this).data("encoded") + "\">" +
                    "<input type=\"hidden\" name=\"csrfmiddlewaretoken\" value=\"" + $("input[name=csrfmiddlewaretoken]").val() + "\">" +
                    "</form>").appendTo("body").submit().remove();
            }
        });

    }
};
