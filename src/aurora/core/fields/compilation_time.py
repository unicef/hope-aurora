from django import forms
from django.conf import settings
from django.forms import widgets

from aurora.core.version_media import VersionMedia


class CompilationTimeWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        _widgets = (
            widgets.HiddenInput(
                attrs={"class": "CompilationTimeField start"},
            ),
            widgets.HiddenInput(
                attrs={"class": "CompilationTimeField elapsed"},
            ),
            widgets.HiddenInput(
                attrs={"class": "CompilationTimeField round"},
            ),
            widgets.HiddenInput(
                attrs={"class": "CompilationTimeField total"},
            ),
        )
        super().__init__(_widgets, attrs)

    @property
    def media(self):
        extra = "" if settings.DEBUG else ".min"
        base = super().media
        return base + VersionMedia(
            js=[
                "admin/js/vendor/jquery/jquery%s.js" % extra,
                "admin/js/jquery.init.js",
                "jquery.compat%s.js" % extra,
                "elapsed%s.js" % extra,
            ],
        )

    def render(self, name, value, attrs=None, renderer=None):
        return super().render(name, value, attrs, renderer)

    def build_attrs(self, base_attrs, extra_attrs=None):
        """Build an attribute dictionary."""
        return {**base_attrs, **(extra_attrs or {})}

    def decompress(self, value):
        if value:
            return value
        return [None, 0, 0, 0]


class CompilationTimeField(forms.CharField):
    widget = CompilationTimeWidget

    def __init__(self, **kwargs):
        kwargs["required"] = False
        kwargs["label"] = ""
        kwargs["help_text"] = ""
        super().__init__(**kwargs)

    def to_python(self, value):
        return dict(zip(["start", "elapsed", "rounds", "total"], value))

    def widget_attrs(self, widget):
        attrs = super().widget_attrs(widget)
        attrs.pop("class", "")
        return attrs
