TODAY = new Date();
dateutil = {
    today: TODAY,
    years18: new Date(new Date().setDate(TODAY.getDate() - (365 * 18))),
    years2: new Date(new Date().setDate(TODAY.getDate() - (365 * 2))),
    getAge: function (birthDate) {
        return Math.floor((new Date() - new Date(birthDate).getTime()) / 3.15576e+10);
    }

};
_ = {
    is_child: function (d) {
        return d && dateutil.getAge(d) < 18
    },
    is_baby: function (d) {
        return d && dateutil.getAge(d) <= 2
    },
    is_future: function (d) {
        return d && Date.parse(d) > dateutil.today
    },
};
_.is_adult = function (d) {
    return !_.is_child(d)
};

smart_fs = {
    getCollector: function (cd) {
        var collectors = cd.filter(e => e.role_i_c === "y");
        if (collectors.length === 1) {
            return collectors[0]
        }
        return null;
    }
}
smart = {
    sameAs: function (sender, target) {
        var $sender = $(sender);
        var $form = $sender.parents(".form-container");
        var $target = $form.find("[data-flex='" + target + "']");
        if ($sender.val() == $target.val()) {
            $sender.css("background-color", "#d7f6ca");
        } else {
            $sender.css("background-color", "#e1adad");
        }
    },
    preventSubmit: function (sender) {
        var $form = $(sender).parents("form");
        var $target = $form.find("input[type=submit]");
        var valid = false;

        if ($(sender).is("input[type=\"checkbox\"]")) {
            valid = $(sender).is(":checked");
        } else if ($(sender).is("input[type=\"radio\"]")) {
            valid = $(sender).val() == "y";
        } else {
            valid = !!$(sender).val();
        }
        if (valid) {
            $target.prop("disabled", false);
        } else {
            $target.prop("disabled", true);
        }
    },
    showHideInForm: function (sender, target, showHide) {
        try {
            var $form = $(sender).parents(".form-container");
            var $target = $form.find(target);
            if (showHide) {
                $target.show();
            } else {
                $target.hide();
            }
        } catch (error) {
            console.error(error);
        }
    },
    setRequiredOnValue: function (sender, targets, value) {
        try {
            console.log(11111, targets)
            var cmp = value.toLowerCase();
            var $form = $(sender).parents(".form-container");
            $form.find(targets).each(function (i, e) {
                $c = $(e).parents(".field-container");
                console.log(11111, $c, $(sender).val(), cmp);
                if ($(sender).val() == cmp) {
                    $(e).attr("required", true);
                    $c.find('.required-label').show();
                } else {
                    $(e).attr("required", false);
                    $c.find('.required-label').hide();
                }
            })
            // if ($(sender).val() == cmp) {
            //     $targets.attr("required", true);
            // } else {
            //     $targets.attr("required", false);
            // }
        } catch (error) {
            console.error(error);
        }
    },
    showHideDependant: function (sender, target, value) {
        try {
            var cmp = value.toLowerCase();
            var $form = $(sender).parents(".form-container");
            var $target = $form.find(target).parents(".field-container");
            if ($(sender).val() == cmp) {
                $target.show();
            } else {
                $target.hide();
            }
            ;
        } catch (error) {
            console.error(error);
        }
    },
    setDependant: function (sender, target, value) {
        try {
            var $form = $(sender).parents(".form-container");
            var $target = $form.find(target);
            $target.prop("disabled", !($(sender).val() == value));
        } catch (error) {
            console.error(error);
        }
    },
    is_adult: function (d) {
        return d && Date.parse(d) <= dateutil.years18 ? true : false;
    },
    handleQuestion: function (e) {
        var $container = $(e).parents("fieldset").find(".field-container");
        if ($(e).is(":checked")) {
            $container.show();
        } else {
            $container.hide();
        }
    },
    updateDeleteLabel: function (sender, label) {
        $(sender).parents(".form-container").find(".delete-button").text(label + $(sender).val());
    }
};