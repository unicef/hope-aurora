(function ($) {
    window._select2 = {
        collect_subscribers: function (e) {
            var $target = $(e);
            var parentName = $target.data("parent");
            $target.data("subscribers", $target.data("subscribers") || []);
            if (parentName) {
                var $formContainer = $target.parents(".form-container");
                var $parent = $formContainer.find("[data-source=" + parentName + "]");
                var subscribers = $parent.data("subscribers") || [];
                subscribers.push($(e).attr("id"));
                $parent.data("subscribers", subscribers);
                $target.data("parentObject", $parent);
            }
        },
        init: function (e) {
            if ($(e).data("select2")) {
                return;
            }
            var $target = $(e);
            var url = $target.data("ajax-url");
            var selected = $target.data("selected");
            var parentName = $target.data("parent");
            var placeholder = $target.data("placeholder");
            var label = $target.data("label");
            var $parent = $target.data("parentObject");
            $target.select2({
                placeholder: placeholder,
                ajax: {
                    minimumInputLength: 2,
                    url: url,
                    dataType: "json",
                    data: function (params) {
                        var query = {
                            q: params.term,
                        };
                        if ($parent) {
                            query.parent = $parent.val();
                        }
                        return query;
                    }
                }
            });
            if (parentName) {
                if (!selected) {
                    $target.prop("disabled", true);
                }
            }

            if (selected) {
                var url = $target.data("ajax--url");
                $.getJSON(url + "?pk=" + selected, function (results) {
                    var data = results.results[0];
                    var newOption = new Option(data.text, data.id, true, true);
                    $target.append(newOption).trigger("change");
                });
            }
        }
    }
    $(function () {
        var CACHE = {};
        var $targets = $(".ajaxSelect");
        console.log("Select2 library loaded", window._select2);
        $targets.each(function (i, e) {
            _select2.collect_subscribers(e);
            // var $target = $(e);
            // var parentName = $target.data("parent");
            // $target.data("subscribers", $target.data("subscribers") || []);
            //
            // if (parentName) {
            //     var $formContainer = $target.parents(".form-container");
            //     var $parent = $formContainer.find("[data-source=" + parentName + "]");
            //     var subscribers = $parent.data("subscribers") || [];
            //     subscribers.push($(e).attr("id"));
            //     $parent.data("subscribers", subscribers);
            //     $target.data("parent", $parent);
            // }
        });
        // var getData = function(url){
        //     $.getJSON(url).then
        // };
        $targets.each(function (i, e) {
            window._select2.init(e);
        });

        $targets.each(function (i, e) {
            $select = $(e);
            if ($select.data("subscribers")) {
                $select.on("change", function (e) {
                    var $self = $(e.target);
                    $self.data("subscribers").forEach(function (e, i) {
                        var child = $("#" + e);
                        if (!child.data("selected")) {
                            child.val("").trigger("change");
                            child.prop("disabled", !$self.val());
                        } else {
                            child.data("selected", "")
                        }
                    });
                });
            }
        });

    });
})($);
