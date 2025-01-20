from django import forms
from django.conf import settings

from aurora.i18n.get_text import gettext as _


class UploadFileWidget(forms.ClearableFileInput):
    template_name = "django/forms/widgets/upload_file.html"
    clear_checkbox_label = _("Clear")
    initial_text = _("Currently")
    input_text = _("Change")

    def render(self, name, value, attrs=None, renderer=None):
        attrs["class"] = (
            "vUploadField "
            "form-control block w-full px-3 py-1.5 text-base font-normal "
            "text-gray-700 bg-white bg-clip-padding border border-solid "
            "border-gray-300 rounded transition ease-in-out m-0 "
            "focus:text-gray-700 focus:bg-white focus:border-blue-600 focus:outline-none"
        )
        return super().render(name, value, attrs, renderer)

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + forms.Media(
            js=[
                "upload/upload%s.js" % extra,
            ],
            css={
                "all": [
                    "upload/upload.css",
                ]
            },
        )


class SmartFileField(forms.FileField):
    widget = UploadFileWidget
    default_error_messages = {
        "invalid": _("No file was submitted. Check the encoding type on the form."),
        "missing": _("No file was submitted."),
        "empty": _("The submitted file is empty."),
        "contradiction": _("Please either submit a file or check the clear checkbox, not both."),
    }
