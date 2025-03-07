(function ($) {
    $(function () {
        var seed = Date.now() + Math.random();
        const slug = $("meta[name=\"Survey\"]").attr("content");
        var userLang = navigator.language || navigator.userLanguage;

        $.get("/register/"+ slug +"/auth/?" + seed).done(function (resp) {
            if (resp.registration) {
                if (resp.registration.protected && resp.user.anonymous) {
                    location.reload();
                }
                $('#loading').addClass("hidden");
                $('#formContainer').removeClass("hidden");
            } else {
                location.href = "/";
            }
        });
    });
})($);
