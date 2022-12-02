(function ($) {
    $(function () {
        var seed = Date.now() + Math.random();
        $.get("../auth/?" + seed).done(function (resp) {
            console.log(111.1, resp.user.username);
            console.log(111.2, resp.registration.protected);
            console.log(111.3, resp.user.anonymous);
            if (resp.registration.protected && resp.user.anonymous){
                location.reload();
            }
            $('#loading').addClass("hidden");
            $('#formContainer').removeClass("hidden");
        });
    });
})($);
