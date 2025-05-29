import logging
from typing import TYPE_CHECKING, Any

from admin_extra_buttons.decorators import button, view
from admin_ordering.admin import OrderableAdmin
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.querystring import QueryStringFilter
from django import forms
from django.contrib import messages
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import JSONField, Model, QuerySet
from django.db.models.functions import Collate
from django.http import HttpRequest, HttpResponse, JsonResponse
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin
from strategy_field import admin  # noqa: E402, I001, F401

from ..admin_sync import SyncMixin
from ..forms import Select2Widget
from ..models import FIELD_KWARGS, FlexFormField
from ..utils import dict_setdefault, is_root, render
from .base import ConcurrencyVersionAdmin
from .field_editor import FieldEditor
from .filters import StrategyFieldSelect2Filter

if TYPE_CHECKING:
    from django.db.models import Field as DBField
    from django.forms import TypedChoiceField
    from django.forms.fields import Field as FormField
    from django.utils.datastructures import _ListOrTuple

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

    def clean(self) -> dict[str, Any] | None:
        ret = super().clean()
        if ret:
            ret.setdefault("advanced", {})
            dict_setdefault(ret["advanced"], FlexFormField.FLEX_FIELD_DEFAULT_ATTRS)
            dict_setdefault(ret["advanced"], {"kwargs": FIELD_KWARGS.get(ret["field_type"], {})})
        return ret


@register(FlexFormField)
class FlexFormFieldAdmin(SyncMixin, ConcurrencyVersionAdmin, OrderableAdmin, SmartModelAdmin[FlexFormField]):
    search_fields = ("name_deterministic", "label")
    list_display = ("label", "name", "flex_form", "type_name", "required", "enabled")
    list_editable = ["required", "enabled"]
    list_filter = (
        ("flex_form", AutoCompleteFilter),
        ("field_type", StrategyFieldSelect2Filter),
        # "field_type",
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

    def get_queryset(self, request: "HttpRequest") -> "QuerySet[FlexFormField]":
        return (
            super()  # type: ignore[return-value]
            .get_queryset(request)
            .annotate(name_deterministic=Collate("name", "und-x-icu"))
            .select_related("flex_form")
        )

    def get_readonly_fields(self, request: "HttpRequest", obj: "Model|None" = None) -> "_ListOrTuple[str]":
        return super().get_readonly_fields(request, obj) if is_root(request) else []

    def formfield_for_dbfield(self, db_field: "DBField", request: "HttpRequest", **kwargs) -> "FormField | None":
        if db_field.name == "advanced":
            kwargs["widget"] = JSONEditor()
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def formfield_for_choice_field(
        self, db_field: "DBField", request: "HttpRequest", **kwargs
    ) -> "TypedChoiceField|None":
        if db_field.name == "field_type":
            kwargs["widget"] = Select2Widget()
            return db_field.formfield(**kwargs)  # type: ignore[return-value]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_changeform_initial_data(self, request: "HttpRequest") -> dict[str, str | list[str] | None]:
        initial = super().get_changeform_initial_data(request)
        current: dict
        if current := initial.get("advanced"):  # type: ignore[assignment]
            ret = FlexFormField.FLEX_FIELD_DEFAULT_ATTRS.copy()
            initial["advanced"] = ret.update(**current)
        else:
            initial["advanced"] = FlexFormField.FLEX_FIELD_DEFAULT_ATTRS  # type: ignore[assignment]
        return initial

    @button(label="editor")  # type: ignore[arg-type]
    def field_editor(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        self.editor = FieldEditor(self, request, pk)
        if request.method == "POST":
            ret = self.editor.post(request, pk)
            self.message_user(request, "Saved", messages.SUCCESS)
            return ret
        return self.editor.get(request, pk)

    @view()  # type: ignore[arg-type]
    def widget_attrs(self, request: "HttpRequest", pk: str) -> HttpResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.get_configuration()
        except Exception as e:
            logger.exception(e)
            return HttpResponse("An internal error has occurred.")

    @view()  # type: ignore[arg-type]
    def widget_refresh(self, request: "HttpRequest", pk: str) -> JsonResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.refresh()
        except Exception as e:
            logger.exception(e)
            return JsonResponse({"Error": "An internal error has occurred."})

    @view()  # type: ignore[arg-type]
    def widget_code(self, request: "HttpRequest", pk: str) -> HttpResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.get_code()
        except Exception as e:
            logger.exception(e)
            return HttpResponse("An internal error has occurred.")

    @view()  # type: ignore[arg-type]
    def widget_display(self, request: "HttpRequest", pk: str) -> HttpResponse:
        try:
            editor = FieldEditor(self, request, pk)
            return editor.render()
        except Exception as e:
            logger.exception(e)
            return HttpResponse("An internal error has occurred.")

    @button()  # type: ignore[arg-type]
    def test(self, request: "HttpRequest", pk: str) -> "HttpResponse":
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
            form_class = type(forms.Form)("TestForm", (forms.Form,), form_class_attrs)  # type: ignore[misc]

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
