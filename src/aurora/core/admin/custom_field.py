import logging
from typing import TYPE_CHECKING

from admin_extra_buttons.decorators import button
from django import forms
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import JSONField, QuerySet
from django.db.models.functions import Collate
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin

from ..models import CustomFieldType
from ..utils import render

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


logger = logging.getLogger(__name__)

cache = caches["default"]


@register(CustomFieldType)
class CustomFieldTypeAdmin(SmartModelAdmin):
    list_display = (
        "name",
        "base_type",
        "attrs",
    )
    search_fields = ("name_deterministic",)
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    def get_queryset(self, request: "HttpRequest") -> "QuerySet":
        return super().get_queryset(request).annotate(name_deterministic=Collate("name", "und-x-icu"))

    @button()  # type: ignore[arg-type]
    def test(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        ctx = self.get_common_context(request, pk)
        fld = ctx["original"]
        field_type = fld.base_type
        kwargs = fld.attrs.copy()
        field = field_type(**kwargs)
        form_class_attrs = {
            "sample": field,
        }
        form_class = type("TestForm", (forms.Form,), form_class_attrs)

        if request.method == "POST":
            form = form_class(request.POST)
            if form.is_valid():
                self.message_user(
                    request,
                    f"Form validation success. You have selected: {form.cleaned_data['sample']}",
                )
        else:
            form = form_class()
        ctx["form"] = form
        return render(request, "admin/core/customfieldtype/test.html", ctx)
