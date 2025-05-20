import logging
from typing import TYPE_CHECKING, Any

from admin_extra_buttons.decorators import button
from concurrency.api import disable_concurrency
from django.conf import settings
from django.core.cache import caches
from reversion_compare.admin import CompareVersionAdmin

from ..admin_sync import is_local
from ..utils import is_root

if TYPE_CHECKING:
    from django.db.models import Model
    from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)

cache = caches["default"]


class ConcurrencyVersionAdmin(CompareVersionAdmin):
    change_list_template = "admin_extra_buttons/change_list.html"

    @button(label="Recover deleted")  # type: ignore[arg-type]
    def _recoverlist_view(self, request: "HttpRequest") -> "HttpResponse":
        return super().recoverlist_view(request)

    def reversion_register(self, model: "Model", **options) -> None:
        options["exclude"] = ("version",)
        super().reversion_register(model, **options)

    def revision_view(
        self, request: "HttpRequest", object_id: str, version_id: int, extra_context: dict[str, Any] | None = None
    ) -> "HttpResponse":
        with disable_concurrency():
            return super().revision_view(request, object_id, version_id, extra_context)

    def recover_view(
        self, request: "HttpRequest", version_id: int, extra_context: dict[str, Any] | None = None
    ) -> "HttpResponse":
        with disable_concurrency():
            return super().recover_view(request, version_id, extra_context)

    def has_change_permission(self, request: "HttpRequest", obj: "Model|None" = None) -> bool:
        orig = super().has_change_permission(request, obj)
        return orig and (settings.DEBUG or is_root(request) or is_local(request))
