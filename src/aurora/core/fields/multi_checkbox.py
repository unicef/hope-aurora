from django import forms

from aurora.core.fields.widgets.mixins import SmartWidgetMixin


class MultiCheckboxWidget(SmartWidgetMixin, forms.CheckboxSelectMultiple):
    template_name = "django/forms/widgets/multi_checkbox.html"
    option_template_name = "django/forms/widgets/multi_checkbox_option.html"
    default_class = ""

    def create_option(self, name, value, label, selected, index, subindex=..., attrs=...):
        ret = super().create_option(name, value, label, selected, index, subindex, attrs)
        ret["attrs"] = {}
        return ret


class MultiCheckboxField(forms.MultipleChoiceField):
    widget = MultiCheckboxWidget
