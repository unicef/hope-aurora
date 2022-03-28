(function ($) {
    $(function () {
        $(".ajaxSelect").each(function (i, e) {
            var $target = $(e);
            var parentName = $target.data("parent");
            $target.data("subscribers", $target.data("subscribers") || []);
            if (parentName){
                var $formContainer = $target.parents(".form-container");
                $parent = $formContainer.find("[data-source=" + parentName + "]");
                var subscribers = $parent.data("subscribers") || [];
                subscribers.push($(e).attr('id'));
                $parent.data("subscribers", subscribers);
            }
        });
        $(".ajaxSelect").each(function (i, e) {
            if ($(e).data("select2")) {
                return;
            }
            var $target = $(e);
            var url = $target.data("ajax-url");
            var selected = $target.data('selected');
            // var source = $target.data("source");
            var parentName = $target.data("parent");
            var label = $target.data("label");
            // var name = $target.data("name");
            // var $formContainer = $target.parents(".form-container");
            var $parent = null;

            $target.select2({
                placeholder: "Select " + label,
                // disabled: true,
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
                if (!selected){
                    $target.prop("disabled", true);
                }
            };

            if (selected){
                var url = $target.data('ajax--url');
                $.getJSON(url + '?pk=' + selected, function (results){
                    var data = results.results[0];
                    var newOption = new Option(data.text, data.id, true, true);
                    $target.append(newOption).trigger('change');
                });
            }

        });
        $(".ajaxSelect").each(function (i, e) {
            $select = $(e);
            if ($select.data('subscribers')){
                $select.on("change", function (e) {
                    var $self = $(e.target);
                    $self.data('subscribers').forEach(function (e, i){
                        $('#' + e).prop("disabled", !$self.val());
                    })
                });
            }
        });

    });
})($);
