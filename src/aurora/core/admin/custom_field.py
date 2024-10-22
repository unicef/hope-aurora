import logging

from django import forms
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import JSONField
from django.db.models.functions import Collate

from admin_extra_buttons.decorators import button
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin

from ..models import CustomFieldType
from ..utils import render

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

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(name_deterministic=Collate("name", "und-x-icu"))
            .select_related("flex_form")
        )

    @button()
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk)
        fld = ctx["original"]
        field_type = fld.base_type
        kwargs = fld.attrs.copy()
        field = field_type(**kwargs)
        form_class_attrs = {
            "sample": field,
        }
        formClass = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)

        if request.method == "POST":
            form = formClass(request.POST)
            if form.is_valid():
                self.message_user(
                    request, f"Form validation success. " f"You have selected: {form.cleaned_data['sample']}"
                )
        else:
            form = formClass()
        ctx["form"] = form
        return render(request, "admin/core/customfieldtype/test.html", ctx)
