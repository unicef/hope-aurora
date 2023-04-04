from django import forms
from django.conf import settings

from .mixins import TailWindMixin
from ...version_media import VersionMedia


class SmartDateWidget(TailWindMixin, forms.DateInput):
    # class Media:
    #     js = [
    #         get_versioned_static_name("datetimepicker/datepicker"s.js"),
    #         # "https://cdnjs.cloudflare.com/ajax/libs/jquery-datetimepicker/2.5.20/jquery.datetimepicker.full.min.js",
    #         get_versioned_static_name("datetimepicker/dt.js"),
    #     ]
    #     css = {"all": [get_versioned_static_name("datetimepicker/datepicker.css")]}

    def __init__(self, attrs=None, format=None):
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
                "admin/js/jquery.init%s.js" % extra,
                "jquery.compat%s.js" % extra,
                "datetimepicker/datepicker%s.js" % extra,
                "datetimepicker/dt%s.js" % extra,
            ],
            css={"all": ["datetimepicker/datepicker.css"]},
        )
