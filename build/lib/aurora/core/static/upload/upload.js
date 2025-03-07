// https://tc39.github.io/ecma262/#sec-array.prototype.includes
if (typeof Object.assign !== "function") {
    Object.assign = function (target, varArgs) {
        "use strict";
        if (target == null) { // TypeError if undefined or null
            throw new TypeError("Cannot convert undefined or null to object");
        }

        var to = Object(target);

        for (var index = 1; index < arguments.length; index++) {
            var nextSource = arguments[index];

            if (nextSource != null) { // Skip over if undefined or null
                for (var nextKey in nextSource) {
                    // Avoid bugs when hasOwnProperty is shadowed
                    if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
                        to[nextKey] = nextSource[nextKey];
                    }
                }
            }
        }
        return to;
    };
}
;
if (!Array.prototype.includes) {
    Object.defineProperty(Array.prototype, "includes", {
        value: function (searchElement, fromIndex) {

            // 1. Let O be ? ToObject(this value).
            if (this == null) {
                throw new TypeError("\"this\" is null or not defined");
            }

            var o = Object(this);

            // 2. Let len be ? ToLength(? Get(O, "length")).
            var len = o.length >>> 0;

            // 3. If len is 0, return false.
            if (len === 0) {
                return false;
            }

            // 4. Let n be ? ToInteger(fromIndex).
            //    (If fromIndex is undefined, this step produces the value 0.)
            var n = fromIndex | 0;

            // 5. If n ≥ 0, then
            //  a. Let k be n.
            // 6. Else n < 0,
            //  a. Let k be len + n.
            //  b. If k < 0, let k be 0.
            var k = Math.max(n >= 0 ? n : len - Math.abs(n), 0);

            // 7. Repeat, while k < len
            while (k < len) {
                // a. Let elementK be the result of ? Get(O, ! ToString(k)).
                // b. If SameValueZero(searchElement, elementK) is true, return true.
                // c. Increase k by 1.
                // NOTE: === provides the correct "SameValueZero" comparison needed here.
                if (o[k] === searchElement) {
                    return true;
                }
                k++;
            }

            // 8. Return false
            return false;
        }
    });
}
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
            if (typeof window.gettext === "undefined") {
                gettext = function (str) {
                    return str;
                };
            }
            var $error = $field.parents(".field-container").find(".size-error");
            var sizeLimit = $field.data("max-size") || M * 10;
            var sizeLimitFormat = gettext("File too big. Max %s ");
            var sizeMax = returnFileSize(sizeLimit);
            var sizeLimitMessage = interpolate(sizeLimitFormat, [sizeMax]);

            $field.on("change", function (e) {
                var file = e.target.files[0];
                $error.html("");
                if (file !== undefined) {
                    // var size = returnFileSize(file.size);
                    if (file.size > sizeLimit) {
                        $field.attr("type", "text");
                        $field.attr("type", "file");
                        $error.html("<ul class=\"errorlist\"><li>" + sizeLimitMessage + "</li></ul>");
                    }
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
