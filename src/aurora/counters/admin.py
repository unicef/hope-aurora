import logging
from typing import TYPE_CHECKING, Iterable

from admin_extra_buttons.decorators import button
from adminfilters.autocomplete import LinkedAutoCompleteFilter
from django.contrib.admin import register
from django.db.transaction import atomic
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.urls import reverse
from smart_admin.modeladmin import SmartModelAdmin

from ..core.utils import is_root
from ..registration.admin.paginator import LargeTablePaginator
from .models import Counter

if TYPE_CHECKING:
    from ..types.http import AuthHttpRequest

logger = logging.getLogger(__name__)


def get_token(request: "AuthHttpRequest") -> str:
    return str(request.user.last_login.utcnow().timestamp())


@register(Counter)
class CounterAdmin(SmartModelAdmin):
    list_display = ("registration", "day", "records")
    list_filter = (
        ("registration__project__organization", LinkedAutoCompleteFilter.factory()),
        (
            "registration__project",
            LinkedAutoCompleteFilter.factory(parent="registration__project__organization"),
        ),
        (
            "registration",
            LinkedAutoCompleteFilter.factory(parent="registration__project"),
        ),
        "day",
    )
    date_hierarchy = "day"
    autocomplete_fields = ("registration",)
    change_form_template = None
    paginator = LargeTablePaginator
    show_full_result_count = False

    def get_exclude(self, request: "HttpRequest", obj: "Counter|None" = None) -> Iterable[str]:
        return ("details",)

    def get_readonly_fields(self, request: "HttpRequest", obj: "Counter|None" = None) -> Iterable[str]:
        if is_root(request):
            return []
        return ("registration", "day", "records")

    def has_add_permission(self, request: "HttpRequest") -> bool:
        return False

    def has_change_permission(self, request: "HttpRequest", obj: "Counter|None" = None) -> bool:
        return is_root(request)

    @button()  # type: ignore[arg-type]
    def chart(self, request: "HttpRequest") -> "HttpResponse":
        return HttpResponseRedirect(reverse("charts:index"))

    @button()  # type: ignore[arg-type]
    def collect(self, request: "HttpRequest") -> "HttpResponse":  # type: ignore[return]
        try:
            with atomic():
                querysets, result = Counter.objects.collect()
                self.message_user(request, str(result))
        except Exception as e:
            logger.exception(e)
            self.message_error_to_user(request, e)
