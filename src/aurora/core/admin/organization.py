import logging

from django.contrib.admin import register
from django.core.cache import caches
from mptt.admin import MPTTModelAdmin

from ..admin_sync import SyncMixin
from ..models import Organization
from .protocols import AuroraSyncOrganizationProtocol

logger = logging.getLogger(__name__)

cache = caches["default"]


@register(Organization)
class OrganizationAdmin(SyncMixin, MPTTModelAdmin):
    list_display = ("name",)
    mptt_level_indent = 20
    mptt_indent_field = "name"
    search_fields = ("name",)
    protocol_class = AuroraSyncOrganizationProtocol
    change_list_template = "admin/core/organization/change_list.html"

    def admin_sync_show_inspect(self):
        return True

    def get_readonly_fields(self, request, obj=None):
        ro = super().get_readonly_fields(request, obj)
        if obj and obj.pk:
            ro = list(ro) + ["slug"]
        return ro
