import logging
from typing import TYPE_CHECKING

from adminfilters.mixin import AdminAutoCompleteSearchMixin
from django.contrib.admin import register
from django.core.cache import caches
from django.db.models.functions import Collate
from mptt.admin import MPTTModelAdmin
from smart_admin.mixins import LinkedObjectsMixin

from ..admin_sync import SyncMixin
from ..models import Organization
from .protocols import AuroraSyncOrganizationProtocol

if TYPE_CHECKING:
    from django.db.models import Model, QuerySet
    from django.http import HttpRequest
    from django.utils.datastructures import _ListOrTuple

logger = logging.getLogger(__name__)

cache = caches["default"]


@register(Organization)
class OrganizationAdmin(SyncMixin, AdminAutoCompleteSearchMixin, LinkedObjectsMixin, MPTTModelAdmin):
    list_display = ("name",)
    mptt_level_indent = 20
    mptt_indent_field = "name"
    search_fields = ("name_deterministic",)
    protocol_class = AuroraSyncOrganizationProtocol
    change_list_template = "admin/core/organization/change_list.html"

    def get_queryset(self, request: "HttpRequest") -> "QuerySet":
        return (
            super()
            .get_queryset(request)
            .annotate(
                name_deterministic=Collate("name", "und-x-icu"),
            )
        )

    def admin_sync_show_inspect(self) -> bool:
        return True

    def get_readonly_fields(self, request: "HttpRequest", obj: "Model|None" = None) -> "_ListOrTuple[str]":
        ro = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            ro = list(ro) + ["slug"]
        return ro
