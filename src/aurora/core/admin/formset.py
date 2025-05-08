import logging
from typing import TYPE_CHECKING

from adminfilters.autocomplete import AutoCompleteFilter
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models import JSONField, QuerySet
from jsoneditor.forms import JSONEditor
from smart_admin.modeladmin import SmartModelAdmin

from ..admin_sync import SyncMixin
from ..models import FormSet

if TYPE_CHECKING:
    from django.http import HttpRequest


logger = logging.getLogger(__name__)

cache = caches["default"]


@register(FormSet)
class FormSetAdmin(SyncMixin, SmartModelAdmin):
    list_display = (
        "name",
        "title",
        "parent",
        "flex_form",
        "enabled",
        "validator",
        "min_num",
        "max_num",
        "extra",
        "dynamic",
    )
    search_fields = ("name", "title")
    list_editable = ("enabled",)
    readonly_fields = ("version", "last_update_date")
    list_filter = (
        ("parent", AutoCompleteFilter),
        ("flex_form", AutoCompleteFilter),
    )
    formfield_overrides = {
        JSONField: {"widget": JSONEditor},
    }

    def get_search_results(
        self, request: "HttpRequest", queryset: "QuerySet", search_term: str
    ) -> "tuple[QuerySet, bool]":
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if "oid" in request.GET:
            queryset = queryset.filter(flex_form__organization__id=request.GET["oid"])
        return queryset, may_have_duplicates
