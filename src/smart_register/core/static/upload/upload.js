;(function ($) {
    $(function () {
        var M = 1048576;

        function returnFileSize(number) {
            if (number < 1024) {
                return number + "bytes";
            } else if (number >= 1024 && number < 1048576) {
                return (number / 1024).toFixed(1) + "KB";
            } else if (number >= 1048576) {
                return (number / 1048576).toFixed(1) + "MB";
            }
        };

        function resizeBase64Img(base64, width, height) {
            var canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            var context = canvas.getContext("2d");
            var deferred = $.Deferred();
            $("<img/>").attr("src", "data:image/gif;base64," + base64).load(function () {
                context.scale(width / this.width, height / this.height);
                context.drawImage(this, 0, 0);
                deferred.resolve($("<img/>").attr("src", canvas.toDataURL()));
            });
            return deferred.promise();
        };
        var UploadHandler = function ($field) {
            var $error = $field.parents(".field-container").find(".size-error");
            var sizeLimit = $field.data("max-size") || M * 10;
            $field.on("change", function (e) {
                var file = e.target.files[0];
                var size = returnFileSize(file.size);
                var sizeMax = returnFileSize(sizeLimit);
                if (file.size > sizeLimit) {
                    $field.attr("type", "text");
                    $field.attr("type", "file");
                    $error.html("<ul class=\"errorlist\"><li>File too big. Max " + sizeMax + "</li></ul>");
                } else {
                    $error.html("");
                }
            });
        };
        var UploadManager = function () {
            var self = this;
            var fields = [];
            self.addField = function (f) {
                var $field = $(f);
                var name = $field.attr("id");
                if (!fields.includes(name)) {
                    $field.data("handler", new UploadHandler($field));
                    fields.push(name);
                }
            };
        };
        window.uploadManager = new UploadManager();

        $("input.vUploadField").each(function () {
            window.uploadManager.addField(this);
        });

    });
})(jQuery);
