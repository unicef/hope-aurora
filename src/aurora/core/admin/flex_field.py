import logging

from admin_extra_buttons.decorators import button, view
from admin_ordering.admin import OrderableAdmin
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.querystring import QueryStringFilter
from django import forms
from django.contrib import messages
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import JSONField
from django.db.models.functions import Collate
from django.http import HttpResponse, JsonResponse
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin

from ...administration.mixin import LoadDumpMixin
from ..admin_sync import SyncMixin
from ..forms import Select2Widget
from ..models import FIELD_KWARGS, FlexFormField
from ..utils import dict_setdefault, is_root, render
from .base import ConcurrencyVersionAdmin
from .field_editor import FieldEditor
from .filters import Select2FieldComboFilter

logger = logging.getLogger(__name__)

cache = caches["default"]


class FlexFormFieldForm(forms.ModelForm):
    class Meta:
        model = FlexFormField
        fields = (
            "version",
            "flex_form",
            "label",
            "name",
            "field_type",
            "choices",
            "required",
            "enabled",
            "validator",
            "validation",
            "regex",
            "advanced",
        )

    def clean(self):
        ret = super().clean()
        ret.setdefault("advanced", {})
        dict_setdefault(ret["advanced"], FlexFormField.FLEX_FIELD_DEFAULT_ATTRS)
        dict_setdefault(ret["advanced"], {"kwargs": FIELD_KWARGS.get(ret["field_type"], {})})
        return ret


@register(FlexFormField)
class FlexFormFieldAdmin(LoadDumpMixin, SyncMixin, ConcurrencyVersionAdmin, OrderableAdmin, SmartModelAdmin):
    search_fields = ("name_deterministic", "label")
    list_display = ("label", "name", "flex_form", "field_type_name", "required", "enabled")
    list_editable = ["required", "enabled"]
    list_filter = (
        ("flex_form", AutoCompleteFilter),
        ("field_type", Select2FieldComboFilter),
        QueryStringFilter,
    )
    autocomplete_fields = ("flex_form", "validator")
    save_as = True
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }
    form = FlexFormFieldForm
    ordering_field = "ordering"
    order = "ordering"
    readonly_fields = ("version", "last_update_date")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(name_deterministic=Collate("name", "und-x-icu"))
            .select_related("flex_form")
        )

    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj) if is_root(request) else []

    def field_type_name(self, obj):
        return obj.field_type.__name__ if obj.field_type else "[[ removed ]]"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "advanced":
            kwargs["widget"] = JSONEditor()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == "field_type":
            kwargs["widget"] = Select2Widget()
            return db_field.formfield(**kwargs)
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial.setdefault("advanced", FlexFormField.FLEX_FIELD_DEFAULT_ATTRS)
        return initial

    @button(label="editor")
    def field_editor(self, request, pk):
        self.editor = FieldEditor(self, request, pk)
        if request.method == "POST":
            ret = self.editor.post(request, pk)
            self.message_user(request, "Saved", messages.SUCCESS)
            return ret
        return self.editor.get(request, pk)

    @view()
    def widget_attrs(self, request, pk) -> HttpResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.get_configuration()
        except Exception as e:
            return HttpResponse(str(e))

    @view()
    def widget_refresh(self, request, pk) -> JsonResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.refresh()
        except Exception as e:
            return JsonResponse({"Error": str(e)})

    @view()
    def widget_code(self, request, pk) -> HttpResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.get_code()
        except Exception as e:
            return HttpResponse(str(e))

    @view()
    def widget_display(self, request, pk) -> HttpResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.render()
        except Exception as e:
            return HttpResponse(str(e))

    @button()
    def test(self, request, pk):
        ctx = self.get_common_context(request, pk)
        try:
            fld = ctx["original"]
            instance = fld.get_instance()
            ctx["debug_info"] = {
                "field_kwargs": fld.get_field_kwargs(),
            }
            form_class_attrs = {
                "sample": instance,
            }
            form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)

            if request.method == "POST":
                form = form_class(request.POST)

                if form.is_valid():
                    ctx["debug_info"]["cleaned_data"] = form.cleaned_data
                    self.message_user(
                        request,
                        f"Form validation success. You have selected: {form.cleaned_data['sample']}",
                    )
            else:
                form = form_class()
            ctx["form"] = form
            ctx["instance"] = instance
        except Exception as e:
            logger.exception(e)
            ctx["error"] = e
            raise

        return render(request, "admin/core/flexformfield/test.html", ctx)
