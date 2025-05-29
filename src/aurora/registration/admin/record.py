import json
import logging
from typing import TYPE_CHECKING, Any, Iterable

from admin_extra_buttons.decorators import button, link
from adminfilters.dates import DateRangeFilter
from adminfilters.filters import AutoCompleteFilter, NumberFilter, ValueFilter
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from smart_admin.modeladmin import SmartModelAdmin

from ...core.utils import is_root
from ..forms import DecryptForm
from .filters import HourFilter
from .paginator import LargeTablePaginator

if TYPE_CHECKING:
    from admin_extra_buttons.buttons import LinkButton
    from django.db.models import QuerySet
    from django.http import HttpRequest, HttpResponse

    from ..models import Record

logger = logging.getLogger(__name__)


class RecordAdmin(SmartModelAdmin):
    search_fields = ("registration__name",)
    list_display = ("timestamp", "remote_ip", "id", "registration", "ignored")
    readonly_fields = (
        "registration",
        "timestamp",
        "remote_ip",
        "id",
        "fields",
        "counters",
    )
    list_filter = (
        ("registration", AutoCompleteFilter),
        ("id", NumberFilter),
        ("timestamp", DateRangeFilter),
        HourFilter,
        ("unique_field", ValueFilter),
        "ignored",
    )
    change_form_template = None
    change_list_template = None
    paginator = LargeTablePaginator
    show_full_result_count = False
    raw_id_fields = [
        "registrar",
        "registration",
    ]

    def get_actions(self, request: "HttpRequest") -> dict:
        return {}

    def get_queryset(self, request: "HttpRequest") -> "QuerySet":
        qs = super().get_queryset(request)
        return qs.select_related("registration", "registrar")

    def get_common_context(self, request: "HttpRequest", pk: str | None = None, **kwargs) -> dict[str, Any]:
        return super().get_common_context(request, pk, is_root=is_root(request), **kwargs)

    def changeform_view(
        self,
        request: "HttpRequest",
        object_id: str | None = None,
        form_url: str = "",
        extra_context: dict[str, Any] = None,
    ) -> "HttpResponse":
        extra_context = {"is_root": is_root(request)}
        return super().changeform_view(request, object_id, form_url, extra_context)

    @link(html_attrs={"class": "aeb-warn "}, change_form=True)
    def receipt(self, button: "LinkButton") -> None:
        try:
            if button.original:
                base = reverse(
                    "register-done",
                    args=[button.original.registration.pk, button.original.pk],
                )
                button.href = base
                button.html_attrs["target"] = f"_{button.original.pk}"
        except Exception as e:
            logger.exception(e)

    @button(label="Preview", permission=is_root)
    def preview(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        ctx = self.get_common_context(request, pk, title="Preview")

        return render(request, "admin/registration/record/preview.html", ctx)

    @button(label="inspect", permission=is_root)
    def inspect(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        ctx = self.get_common_context(request, pk, title="Inspect")
        if self.object.files:
            ctx["files_as_dict"] = json.loads(self.object.files.tobytes().decode())
        return render(request, "admin/registration/record/inspect.html", ctx)

    @button(permission=is_root)
    def decrypt(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        ctx = self.get_common_context(request, pk, title="To decrypt you need to provide Registration Private Key")
        if request.method == "POST":
            form = DecryptForm(request.POST)
            ctx["title"] = "Data have been decrypted only to be showed on this page. Still encrypted on the DB"
            if form.is_valid():
                key = form.cleaned_data["key"]
                try:
                    ctx["decrypted"] = self.object.decrypt(key)
                except Exception as e:
                    ctx["title"] = "Error decrypting data"
                    self.message_error_to_user(request, e)
        else:
            form = DecryptForm()

        ctx["form"] = form
        return render(request, "admin/registration/record/decrypt.html", ctx)

    def get_readonly_fields(self, request: "HttpRequest", obj: "Record|None" = None) -> Iterable[str]:
        if is_root(request) or settings.DEBUG:
            return []
        return self.readonly_fields

    def has_view_permission(self, request: "HttpRequest", obj: "Record|None" = None) -> bool:
        return is_root(request) or settings.DEBUG

    def has_add_permission(self, request: "HttpRequest") -> bool:
        return is_root(request) or settings.DEBUG

    def has_delete_permission(self, request: "HttpRequest", obj: "Record|None" = None) -> bool:
        return settings.DEBUG

    def has_change_permission(self, request: "HttpRequest", obj: "Record|None" = None) -> bool:
        return is_root(request) or settings.DEBUG
