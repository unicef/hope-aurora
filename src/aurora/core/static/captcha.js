function Captcha() {
    const self = this;
    const NUMBERS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9];
    const TYPES = ["bw", "wb"];
    const ORIENTATION = ["l", "r"];
    var random = function (arr) {
        return arr[(Math.floor(Math.random() * (arr.length)))]
    }
    var randInt = function (max) {
        return Math.floor(Math.random() * max);
    }

    var randomImage = function (n) {
        var ret = [];
        var s = n.toString();
        for (let i = 0; i < n.toString().length; i++) {
            ret.push(s[i] + random(TYPES) + random(ORIENTATION) + ".jpg")
        }
        return ret;
    }
    let a, b, result;

    self.refresh = function () {
        a = randInt(99);
        b = randInt(9);
        result = (a + b).toString();
        $("#captcha0, #captcha1").html('');
        $.each(randomImage(a), function (i, e) {
            var src = '<img class="inline" width="30" src="/static/captcha/' + e + '">';
            $("#captcha0").append(src);
        });

        $.each(randomImage(b), function (i, e) {
            var src = '<img class="inline" width="30" src="/static/captcha/' + e + '">';
            $("#captcha1").append(src);
        });
    };

    self.init = function () {
        const $submit = $("input[type=submit]");
        $('#captcha input').on("keyup", function (i, e) {
            const correct = $(this).val() === result;
            $submit.attr("disabled", !correct);
        });
        $('#registrationForm').on("submit", function (){
            return false;
        })
        self.refresh()
    }// init()
}

window.captcha = new Captcha();
