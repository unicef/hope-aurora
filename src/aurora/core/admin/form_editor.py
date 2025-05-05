import json
from typing import TYPE_CHECKING, Any

from django import forms
from django.core.cache import caches
from django.forms import Media
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.functional import cached_property

from admin_extra_buttons.mixins import ExtraButtonsMixin
from aurora.core.admin.editor import FlexEditor
from aurora.core.fields.widgets import JavascriptEditor
from aurora.core.models import FlexForm

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin
    from django.http import HttpRequest


cache = caches["default"]


class AdvancendAttrsMixin(FlexEditor):
    def __init__(self, *args, **kwargs) -> None:
        self.form = kwargs.pop("form", None)
        super().__init__(*args, **kwargs)


class FlexFormAttributesForm(AdvancendAttrsMixin, forms.ModelForm):
    class Meta:
        model = FlexForm
        fields = (
            "name",
            "base_type",
        )


class EventForm(AdvancendAttrsMixin, forms.Form):
    onsubmit = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    onload = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)
    validation = forms.CharField(widget=JavascriptEditor(toolbar=True), required=False)


DEFAULTS = {}


def get_initial(form: "FlexForm", prefix: str) -> dict[str, Any]:
    return DEFAULTS.get(prefix, {})


class FormEditor:
    FORMS = {
        "frm": FlexFormAttributesForm,
        "events": EventForm,
    }

    def __init__(self, modeladmin: "ExtraButtonsMixin", request: "HttpRequest", pk: str) -> None:
        self.modeladmin = modeladmin
        self.request = request
        self.pk = pk
        self.cache_key = f"/editor/form/{self.request.user.pk}/{self.pk}/"

    @cached_property
    def flex_form(self) -> FlexForm:
        return FlexForm.objects.get(pk=self.pk)

    @cached_property
    def patched_form(self) -> FlexForm:
        return self.flex_form.get_form_class()

    def get_configuration(self) -> "HttpResponse":
        self.patched_form.get_instance()
        rendered = json.dumps(self.flex_form.advanced, indent=4)
        return HttpResponse(rendered, content_type="text/plain")

    def get_code(self) -> "HttpResponse":
        from bs4 import BeautifulSoup, formatter
        from pygments import highlight
        from pygments.formatters.html import HtmlFormatter
        from pygments.lexers import HtmlLexer

        instance = self.patched_form()
        ctx = self.get_context(self.request)
        ctx["form"] = self.flex_form.get_form_class()
        ctx["instance"] = instance
        code = get_template("smart/_form.html").render(ctx)
        formatter = formatter.HTMLFormatter(indent=2)
        soup = BeautifulSoup(code)
        pretty_html = soup.prettify(formatter=formatter)

        formatter = HtmlFormatter(style="default", full=True)
        ctx["code"] = highlight(pretty_html, HtmlLexer(), formatter)
        return render(
            self.request,
            "admin/core/flexformfield/field_editor/code.html",
            ctx,
            content_type="text/html",
        )

    def render(self) -> "HttpResponse":
        instance = self.patched_form
        form_class = self.flex_form.get_form_class()
        ctx = self.get_context(self.request)
        if self.request.method == "POST":
            form = form_class(self.request.POST)
            ctx["valid"] = form.is_valid()
        else:
            form = form_class()
            ctx["valid"] = None

        ctx["form"] = form
        ctx["instance"] = instance

        return render(self.request, "admin/core/flexform/form_editor/preview.html", ctx)

    def get_forms(self, data: dict[str, Any] | None = None) -> dict:
        if data:
            return {prefix: Form(data, prefix=prefix, form=self.flex_form) for prefix, Form in self.FORMS.items()}
        if self.request.method == "POST":
            return {
                prefix: Form(
                    self.request.POST,
                    prefix=prefix,
                    form=self.flex_form,
                    initial=get_initial(self.flex_form, prefix),
                )
                for prefix, Form in self.FORMS.items()
            }
        return {
            prefix: Form(
                prefix=prefix,
                form=self.flex_form,
                initial=get_initial(self.flex_form, prefix),
            )
            for prefix, Form in self.FORMS.items()
        }

    def refresh(self) -> JsonResponse:
        forms = self.get_forms()
        if all(f.is_valid() for f in forms.values()):
            data = self.request.POST.dict()
            data.pop("csrfmiddlewaretoken")
            cache.set(self.cache_key, data)
        else:
            return JsonResponse({prefix: frm.errors for prefix, frm in forms.items()}, status=400)
        return JsonResponse(data)

    def get_context(self, request: "HttpRequest", pk: str | None = None, **kwargs) -> dict[str, Any]:
        return {
            **self.modeladmin.get_common_context(request, pk),
            **kwargs,
        }

    def get(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        ctx = self.get_context(request, pk)
        ctx["forms_media"] = Media()
        for prefix, frm in self.get_forms().items():
            ctx[f"form_{prefix}"] = frm
            ctx["forms_media"] += frm.media
        return render(request, "admin/core/flexform/form_editor/main.html", ctx)

    def post(self, request: "HttpRequest", pk: str | None = None) -> "HttpResponse | None":
        forms = self.get_forms()
        if all(f.is_valid() for f in forms.values()):
            return HttpResponseRedirect(".")
        return None
