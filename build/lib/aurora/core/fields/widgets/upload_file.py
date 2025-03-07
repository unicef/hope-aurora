from django import forms
from django.conf import settings


class UploadFileWidget(forms.ClearableFileInput):
    template_name = "django/forms/widgets/upload_file.html"

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
