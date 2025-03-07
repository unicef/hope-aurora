import logging

from admin_extra_buttons.decorators import button
from admin_sync.utils import is_local
from concurrency.api import disable_concurrency
from django.conf import settings
from django.core.cache import caches
from reversion_compare.admin import CompareVersionAdmin

from ..utils import is_root

logger = logging.getLogger(__name__)

cache = caches["default"]


class ConcurrencyVersionAdmin(CompareVersionAdmin):
    change_list_template = "admin_extra_buttons/change_list.html"

    @button(label="Recover deleted")
    def _recoverlist_view(self, request):
        return super().recoverlist_view(request)

    def reversion_register(self, model, **options):
        options["exclude"] = ("version",)
        super().reversion_register(model, **options)

    def revision_view(self, request, object_id, version_id, extra_context=None):
        with disable_concurrency():
            return super().revision_view(request, object_id, version_id, extra_context)

    def recover_view(self, request, version_id, extra_context=None):
        with disable_concurrency():
            return super().recover_view(request, version_id, extra_context)

    def has_change_permission(self, request, obj=None):
        orig = super().has_change_permission(request, obj)
        return orig and (settings.DEBUG or is_root(request) or is_local(request))
