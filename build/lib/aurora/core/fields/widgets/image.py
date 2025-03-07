from django import forms

from aurora.i18n.get_text import gettext as _


class ImageWidget(forms.ClearableFileInput):
    template_name = "django/forms/widgets/image.html"
    clear_checkbox_label = _("Clear")
    initial_text = _("Currently")
    input_text = _("Change")

    def render(self, name, value, attrs=None, renderer=None):
        attrs["class"] = (
            "form-control block w-full px-3 py-1.5 text-base font-normal "
            "text-gray-700 bg-white bg-clip-padding border border-solid "
            "border-gray-300 rounded transition ease-in-out m-0 "
            "focus:text-gray-700 focus:bg-white focus:border-blue-600 focus:outline-none"
        )
        return super().render(name, value, attrs, renderer)
