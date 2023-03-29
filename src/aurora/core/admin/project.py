import logging

from django.contrib.admin import register
from django.core.cache import caches
from mptt.admin import MPTTModelAdmin
from smart_admin.mixins import LinkedObjectsMixin

from ..admin_sync import SyncMixin
from ..models import Project
from .protocols import AuroraSyncProjectProtocol

logger = logging.getLogger(__name__)

cache = caches["default"]


@register(Project)
class ProjectAdmin(SyncMixin, LinkedObjectsMixin, MPTTModelAdmin):
    list_display = ("name",)
    list_filter = ("organization",)
    mptt_level_indent = 20
    mptt_indent_field = "name"
    search_fields = ("name",)
    protocol_class = AuroraSyncProjectProtocol
    autocomplete_fields = "parent, "

    def get_search_results(self, request, queryset, search_term):
        queryset, may_have_duplicates = super().get_search_results(request, queryset, search_term)
        if "oid" in request.GET:
            queryset = queryset.filter(organization__id=request.GET["oid"])
        return queryset, may_have_duplicates

    def get_readonly_fields(self, request, obj=None):
        ro = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            ro = list(ro) + ["slug"]
        return ro
