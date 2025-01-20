from django import forms

from aurora.core.utils import get_versioned_static_name


class PictureWidget(forms.Textarea):
    template_name = "django/forms/widgets/picture.html"

    class Media:
        js = [
            get_versioned_static_name("webcam/webcam.js"),
        ]
        css = {"all": [get_versioned_static_name("webcam/webcam.css")]}

    def __init__(self, attrs=None):
        attrs = {"class": "vPictureField", **(attrs or {})}
        super().__init__(attrs=attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        return super().build_attrs(base_attrs, extra_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget as an HTML string."""
        context = self.get_context(name, value, attrs)
        label1 = context["widget"]["attrs"].get("smart_attrs", {}).get("label-button", "Take Photo")
        label2 = context["widget"]["attrs"].get("smart_attrs", {}).get("label-cancel", "Cancel Photo")
        context["buttonLabel"] = label1
        context["cancelLabel"] = label2
        return self._render(self.template_name, context, renderer)
