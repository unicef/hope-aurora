from django import forms
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from django.utils.safestring import mark_safe



class PythonEditor(forms.Textarea):
    template_name = "steficon/widgets/codewidget.html"

    def __init__(self, *args, **kwargs):
        theme = kwargs.pop("theme", "midnight")
        super().__init__(*args, **kwargs)
        self.attrs["class"] = "python-editor"
        self.attrs["theme"] = theme

    class Media:
        css = {
            "all": (
                static("admin/steficon/codemirror/codemirror.css"),
                static("admin/steficon/codemirror/fullscreen.css"),
                static("admin/steficon/codemirror/midnight.css"),
                static("admin/steficon/codemirror/foldgutter.css"),
            )
        }
        js = (
            static("admin/steficon/codemirror/codemirror.js"),
            static("admin/steficon/codemirror/python.js"),
            # static("admin/steficon/codemirror/javascript.js"),
            static("admin/steficon/codemirror/fullscreen.js"),
            static("admin/steficon/codemirror/active-line.js"),
            static("admin/steficon/codemirror/foldcode.js"),
            static("admin/steficon/codemirror/foldgutter.js"),
            static("admin/steficon/codemirror/indent-fold.js"),
        )


class ContentTypeChoiceField(forms.ModelChoiceField):
    def __init__(
        self,
        *,
        empty_label="---------",
        required=True,
        widget=None,
        label=None,
        initial=None,
        help_text="",
        to_field_name=None,
        limit_choices_to=None,
        **kwargs,
    ):
        queryset = ContentType.objects.order_by("model", "app_label")
        super().__init__(
            queryset,
            empty_label=empty_label,
            required=required,
            widget=widget,
            label=label,
            initial=initial,
            help_text=help_text,
            to_field_name=to_field_name,
            limit_choices_to=limit_choices_to,
            **kwargs,
        )

    def label_from_instance(self, obj):
        return f"{obj.name.title()} ({obj.app_label})"


class JsonWidget(forms.widgets.TextInput):
    template_name = "steficon/json.html"

    class Media:
        # js = (
        #     settings.MEDIA_URL + 'js/rating.js',
        # )

        css = {"screen": ("administration/pygments.css",)}

    def get_context(self, name, value, attrs):
        import json

        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import JsonLexer

        json_object = json.loads(value)
        json_str = json.dumps(json_object, indent=4, sort_keys=True)

        context = {
            "json_pretty": mark_safe(highlight(json_str, JsonLexer(), HtmlFormatter(style="colorful", wrapcode=True))),
            # 'json_pretty': mark_safe(highlight(json_str, JsonLexer(), HtmlFormatter(wrapcode=True))),
            "widget": {
                "name": name,
                "is_hidden": self.is_hidden,
                "required": self.is_required,
                "value": self.format_value(value),
                "attrs": self.build_attrs(self.attrs, attrs),
                "template_name": self.template_name,
            },
        }
        return context
