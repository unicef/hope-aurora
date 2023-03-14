window.aurora = {
    Field: function (origin) {
        var self = this;
        self.origin = origin;
        const $me = $(origin);
        const $fieldset = $me.parents('fieldset');
        const id = $fieldset.data("fid");
        const $form = $me.parents('form');
        const $fieldContainer = $me.parents('.field-container');
        const $formContainer = $me.parents('.form-container');
        const $input = $fieldset.find(`#${id}`);
        const initial = {
            required: $input.attr("required"),
        }
        self.setRequired = function (onOff) {
            $input.attr("required", onOff);
            onOff ? $fieldset.find('.required-label').show() : $fieldset.find('.required-label').hide();
            return self;
        };
        self.hide = function () {
            $fieldContainer.hide();
            return self;
        };
        self.show = function () {
            $fieldContainer.show();
            return self;
        };
        self.toggle = function (value) {
            $fieldContainer.toggle();
            if (!$fieldContainer.is(":visible")) {
                self.setRequired(false);
            } else {
                self.setRequired(initial.required);
            }
            return self;
        };
        self.setValue = function (value) {
            $input.val(value);
            return self;
        };
        self.hasValue = function () {
            var inputType = $input.attr('type')
            if ((inputType === "radio") || (inputType === "checkbox")) {
                $input.is(":checked");
            } else {
                return $input.val().trim() !== '';
            }
        };
        self.getValue = function () {
            return $input.val();
        };
        self.setDescription = function (value) {
            $fieldset.find('.description').text(value);
            return self;
        };
        self.setHint = function (value) {
            $fieldset.find('.hint').text(value);
            return self;
        };
        self.sibling = function (name) {
            var target = $formContainer.find(`input[name=${name}]`);
            return new aurora.Field(target);
        };
        self.setRequiredOnValue = function (value, targets) {
            try {
                const cmp = value.toString().toLowerCase();
                const val = self.getValue();
                $form.find(targets).each(function (i, e) {
                    var $c = $(e).parents(".field-container");
                    if (val == cmp) {
                        $(e).attr("required", true);
                        $c.find('.required-label').show();
                    } else {
                        $(e).attr("required", false);
                        $c.find('.required-label').hide();
                    }
                })
            } catch (error) {
                console.error(error);
            }
        };
        self.inspect = function () {
            console.log(2222, {
                id: id,
                me: $me,
                form: $form,
                fieldset: $fieldset,
                input: $input,
            })
        };
    }
};
