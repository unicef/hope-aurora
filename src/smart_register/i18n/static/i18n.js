$("#set_language").on("change", function () {
    $('<form action="'+$(this).data("url") +'" method="post">' +
        '<input type="hidden" name="language" value="'+ $(this).val()+'">' +
        '<input type="hidden" name="csrfmiddlewaretoken" value="'+ $("input[name=csrfmiddlewaretoken]").val()+'">' +
        '</form>').appendTo('body').submit().remove();
}).parent().show();
