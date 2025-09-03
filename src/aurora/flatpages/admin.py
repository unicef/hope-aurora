from typing import TYPE_CHECKING, Any

from admin_extra_buttons.decorators import button, view
from django.conf import settings
from django.shortcuts import render
from smart_admin.modeladmin import SmartModelAdmin

from aurora.core.admin_sync import SyncModelAdmin

from .forms import FlatPageForm

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


INITIAL_CONTENT = """

"""


class FlatPageAdmin(SyncModelAdmin, SmartModelAdmin):
    form = FlatPageForm
    list_display = (
        "title",
        "url",
    )
    list_filter = ("sites", "registration_required")
    filter_horizontal = ("sites",)
    search_fields = ("url", "title")
    save_on_top = True

    def get_changeform_initial_data(self, request: "HttpRequest") -> dict[str, Any]:
        initial = super().get_changeform_initial_data(request)
        initial["content"] = INITIAL_CONTENT
        initial["sites"] = settings.SITE_ID
        return initial

    @view()
    def xrender(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        obj = self.get_object(request, pk)
        from aurora.flatpages.views import render_flatpage

        return render_flatpage(request, obj)

    @button()
    def preview(self, request: "HttpRequest", pk: str) -> "HttpResponse":
        ctx = self.get_common_context(request, pk, title="Preview")
        return render(request, "admin/flatpages/flatpage/preview.html", ctx)
