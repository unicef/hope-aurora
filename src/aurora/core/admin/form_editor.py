import json
from typing import Dict

from django import forms
from django.core.cache import caches
from django.forms import Media
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import get_template
from django.utils.functional import cached_property

from aurora.core.fields.widgets import JavascriptEditor
from aurora.core.models import FlexForm

cache = caches["default"]


class AdvancendAttrsMixin:
    def __init__(self, *args, **kwargs):
        self.form = kwargs.pop("form", None)
        super().__init__(*args, **kwargs)


#
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


DEFAULTS = {
    #     "css": {"question": "cursor-pointer", "label": "block uppercase tracking-wide text-gray-700 font-bold mb-2"},
    #     "css": {"question": "cursor-pointer", "label": "block uppercase tracking-wide text-gray-700 font-bold mb-2"},
}


def get_initial(field, prefix):
    base = DEFAULTS.get(prefix, {})
    for k, v in field.advanced.get(prefix, {}).items():
        if v:
            base[k] = v
    return base


class FormEditor:
    FORMS = {
        "frm": FlexFormAttributesForm,
        # "kwargs": FormFieldAttributesForm,
        # "widget": WidgetAttributesForm,
        # "smart": SmartAttributesForm,
        # "css": CssForm,
        "events": EventForm,
    }

    def __init__(self, modeladmin, request, pk):
        self.modeladmin = modeladmin
        self.request = request
        self.pk = pk
        self.cache_key = f"/editor/form/{self.request.user.pk}/{self.pk}/"

    @cached_property
    def flex_form(self):
        return FlexForm.objects.get(pk=self.pk)

    @cached_property
    def patched_form(self):
        fld = self.flex_form.get_form_class()
        # if config := cache.get(self.cache_key, None):
        #     forms = self.get_forms(config)
        #     fieldForm = forms.pop("field", None)
        #     if fieldForm.is_valid():
        #         for k, v in fieldForm.cleaned_data.items():
        #             setattr(fld, k, v)
        #     for prefix, frm in forms.items():
        #         frm.is_valid()
        #         merged = merge_data(fld.advanced, {**{prefix: frm.cleaned_data}})
        #         fld.advanced = merged
        return fld

    def patch(self, request, pk):
        pass

    def get_configuration(self):
        self.patched_form.get_instance()
        rendered = json.dumps(self.flex_form.advanced, indent=4)
        return HttpResponse(rendered, content_type="text/plain")

    def get_code(self):
        from bs4 import BeautifulSoup as bs
        from bs4 import formatter
        from pygments import highlight
        from pygments.formatters.html import HtmlFormatter
        from pygments.lexers import HtmlLexer

        instance = self.patched_form()
        # form_class_attrs = {
        #     self.field.name: instance,
        # }
        # form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)
        ctx = self.get_context(self.request)
        ctx["form"] = self.flex_form.get_form_class()
        ctx["instance"] = instance
        # code = Template(
        #     "{{ form }}"
        # ).render(Context(ctx))
        code = get_template("smart/_form.html").render(ctx)
        formatter = formatter.HTMLFormatter(indent=2)
        soup = bs(code)
        prettyHTML = soup.prettify(formatter=formatter)

        formatter = HtmlFormatter(style="default", full=True)
        ctx["code"] = highlight(prettyHTML, HtmlLexer(), formatter)
        return render(self.request, "admin/core/flexformfield/field_editor/code.html", ctx, content_type="text/html")

    def render(self):
        instance = self.patched_form
        # form_class_attrs = {
        #     'fo': instance,
        # }
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

    def get_forms(self, data=None) -> Dict:
        if data:
            return {prefix: Form(data, prefix=prefix, form=self.flex_form) for prefix, Form in self.FORMS.items()}
        if self.request.method == "POST":
            return {
                prefix: Form(
                    self.request.POST, prefix=prefix, form=self.flex_form, initial=get_initial(self.field, prefix)
                )
                for prefix, Form in self.FORMS.items()
            }
        return {
            prefix: Form(prefix=prefix, form=self.flex_form, initial=get_initial(self.flex_form, prefix))
            for prefix, Form in self.FORMS.items()
        }

    def refresh(self):
        forms = self.get_forms()
        if all(map(lambda f: f.is_valid(), forms.values())):
            data = self.request.POST.dict()
            data.pop("csrfmiddlewaretoken")
            cache.set(self.cache_key, data)
        else:
            return JsonResponse({prefix: frm.errors for prefix, frm in forms.items()}, status=400)
        return JsonResponse(data)

    def get_context(self, request, pk=None, **kwargs):
        return {
            **self.modeladmin.get_common_context(request, pk),
            **kwargs,
        }

    def get(self, request, pk):
        ctx = self.get_context(request, pk)
        ctx["forms_media"] = Media()
        for prefix, frm in self.get_forms().items():
            ctx[f"form_{prefix}"] = frm
            ctx["forms_media"] += frm.media
        return render(request, "admin/core/flexform/form_editor/main.html", ctx)

    def post(self, request, pk):
        forms = self.get_forms()
        if all(map(lambda f: f.is_valid(), forms.values())):
            self.patched_field.save()
            return HttpResponseRedirect(".")
