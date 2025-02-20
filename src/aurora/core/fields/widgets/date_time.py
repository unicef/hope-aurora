from django import forms
from django.conf import settings

from ...version_media import VersionMedia
from .mixins import TailWindMixin


class SmartDateWidget(TailWindMixin, forms.DateInput):
    def __init__(self, attrs=None, format=None):  # noqa
        super().__init__(attrs=attrs, format=format)
        self.attrs.setdefault("class", {})
        self.attrs["class"] += " vDateField "
        self.attrs["size"] = 10

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + VersionMedia(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "datetimepicker/datepicker%s.js" % extra,
                "datetimepicker/dt%s.js" % extra,
            ],
            css={"all": ["datetimepicker/datepicker.css"]},
        )
