import json
from typing import TYPE_CHECKING, Any, ClassVar, reveal_type

from admin_extra_buttons.mixins import ExtraButtonsMixin
from django import forms
from django.core.cache import caches
from django.forms import Form, Media
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.functional import cached_property

from aurora.core.admin.editor import FlexEditor
from aurora.core.fields.widgets import JavascriptEditor
from aurora.core.forms import FlexFormBaseForm
from aurora.core.models import FlexForm, FlexFormField

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin
    from django.http import HttpRequest

    from aurora.types.core.admin.form_editor import FormEditorForms, FormEditorTypes
    from aurora.types.core.models import FlexFormForm

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


DEFAULTS: dict[str, Any] = {}


def get_initial(form: "FlexForm", prefix: str) -> dict[str, Any]:
    base = DEFAULTS.get(prefix, {})
    for k, v in form.advanced.get(prefix, {}).items():
        if v:
            base[k] = v
    return base


class FormEditor:
    FORMS: "dict[str, FormEditorTypes]" = {
        "frm": FlexFormAttributesForm,
        "events": EventForm,
    }

    def __init__(self, modeladmin: "ExtraButtonsMixin", request: "HttpRequest", pk: str) -> None:
        self.modeladmin = modeladmin
        self.request = request
        self.pk = pk
        self.errors: dict[str, list[str]] = {}
        self.cache_key = f"/editor/form/{self.request.user.pk}/{self.pk}/"

    @cached_property
    def flex_form(self) -> FlexForm:
        return FlexForm.objects.get(pk=self.pk)

    @cached_property
    def patched_form(self) -> "type[FlexFormBaseForm]":
        return self.flex_form.get_form_class()

    def get_configuration(self) -> "HttpResponse":
        return HttpResponse("aaaa", content_type="text/plain")
        # self.patched_form.get_instance()
        # rendered = json.dumps(self.flex_form.advanced, indent=4)
        # return HttpResponse(rendered, content_type="text/plain")

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
        formatter1 = formatter.HTMLFormatter(indent=2)
        soup = BeautifulSoup(code, features="lxml")
        pretty_html = soup.prettify(formatter=formatter1)

        formatter2 = HtmlFormatter(style="default", full=True)
        ctx["code"] = highlight(pretty_html, HtmlLexer(), formatter2)
        return render(
            self.request,
            "admin/core/flexform/form_editor/code.html",
            ctx,
            content_type="text/html",
        )

    def render(self) -> "HttpResponse":
        instance = self.patched_form
        form_class: type[FlexFormBaseForm] = self.flex_form.get_form_class()
        ctx = self.get_context(self.request)
        if self.request.method == "POST":
            form = form_class(self.request.POST)
            ctx["valid"] = self.is_valid()
        else:
            form = form_class()
            ctx["valid"] = None

        ctx["form"] = form
        ctx["instance"] = instance
        return render(self.request, "admin/core/flexform/form_editor/render.html", ctx)

    def get_forms(self, data: dict[str, Any] | None = None) -> "FormEditorForms":
        ret: FormEditorForms
        # Form: FlexFormAttributesForm | EventForm
        if data:
            ret = {
                prefix: Form(
                    data,  # type: ignore[assignment]
                    prefix=prefix,
                    form=self.flex_form,
                )
                for prefix, Form in self.FORMS.items()
            }
        elif self.request.method == "POST":
            ret = {  # type: ignore[assignment]
                prefix: Form(
                    self.request.POST,
                    prefix=prefix,
                    form=self.flex_form,
                    initial=get_initial(self.flex_form, prefix),
                )
                for prefix, Form in self.FORMS.items()
            }
        else:
            ret = {  # type: ignore[assignment]
                prefix: Form(
                    prefix=prefix,
                    form=self.flex_form,
                    initial=get_initial(self.flex_form, prefix),
                )
                for prefix, Form in self.FORMS.items()
            }
        return ret

    def is_valid(self) -> bool:
        forms: FormEditorForms = self.get_forms()
        if all(f.is_valid() for f in forms.values()):  # type: ignore[attr-defined]
            return True
        else:
            self.errors = {prefix: frm.errors for prefix, frm in forms.items()}  # type: ignore[attr-defined]
            return False

    def refresh(self) -> JsonResponse:
        if self.is_valid():
            data = self.request.POST.dict()
            data.pop("csrfmiddlewaretoken")
            return JsonResponse(data)
        else:
            return JsonResponse(self.errors, status=400)

    #
    # forms: FormEditorForms = self.get_forms()
    # if all(f.is_valid() for f in forms.values()):
    #     data = self.request.POST.dict()
    #     data.pop("csrfmiddlewaretoken")
    #     cache.set(self.cache_key, data)
    # else:
    #     return JsonResponse({prefix: frm.errors for prefix, frm in forms.items()}, status=400)
    # return JsonResponse(data)

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
            ctx["forms_media"] += frm.media  # type: ignore[attr-defined]
        return render(request, "admin/core/flexform/form_editor/main.html", ctx)

    def post(self, request: "HttpRequest", pk: str | None = None) -> "HttpResponseRedirect | None":
        # forms: FormEditorForms = self.get_forms()
        # if all(f.is_valid() for f in forms.values()):
        if self.is_valid():
            return HttpResponseRedirect(".")
        return None
