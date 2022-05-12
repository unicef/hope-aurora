(function ($) {
    $(function () {
        // we need this HACK to manage the stupid cache system in front of the app
        const slug = $("meta[name=\"Survey\"]").attr("content");
        $.get("/api/registration/" + slug + "/version/?" + Math.random(), function (data) {
            var parts = location.href.split("/");
            const version = parseInt(parts[parts.length - 2]);
            if (version !== data.version) {
                var url = null;
                if (isNaN(version)) {
                    parts[parts.length - 1] = data.version;
                    parts.push('')
                } else {
                    parts[parts.length - 2] = data.version;
                }
                url = parts.join("/");
                location.href = url;
            }
        });
    });
})($);
