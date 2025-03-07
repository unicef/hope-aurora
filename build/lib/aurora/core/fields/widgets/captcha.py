from django.forms import widgets

from .mixins import SmartWidgetMixin, TailWindMixin


class CaptchaWidget(SmartWidgetMixin, TailWindMixin, widgets.TextInput):
    template_name = "django/forms/widgets/captcha.html"

    class Media:
        js = ("captcha.js",)

    def build_attrs(self, base_attrs, extra_attrs=None):
        base_attrs["data-onload"] = "captcha.init();"
        return super().build_attrs(base_attrs, extra_attrs)
