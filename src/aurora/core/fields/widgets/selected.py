from django.conf import settings
from django import forms

from aurora.core.fields.mixins import TailWindMixin
from aurora.core.version_media import VersionMedia


class SmartChoiceWidget(TailWindMixin, forms.Select):
    template_name = "django/forms/widgets/smart_select.html"


class SmartSelectWidget(TailWindMixin, forms.Select):
    template_name = "django/forms/widgets/smart_select.html"


class AjaxSelectWidget(TailWindMixin, forms.Select):
    template_name = "django/forms/widgets/ajax_select.html"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs)
        self.attrs.setdefault("class", {})

    def build_attrs(self, base_attrs, extra_attrs=None):
        base_attrs["class"] += " ajaxSelect"
        return super().build_attrs(base_attrs, extra_attrs)

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + VersionMedia(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "https://cdnjs.cloudflare.com/ajax/libs/select2/4.1.0-rc.0/js/select2.min.js",
                "select2/ajax_select%s.js" % extra,
                "jquery.formset%s.js" % extra,
                "smart.formset%s.js" % extra,
            ],
            css={
                "all": [
                    "select2/select2.min.css",
                ]
            },
        )