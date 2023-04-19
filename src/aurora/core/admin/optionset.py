import logging

from admin_extra_buttons.decorators import button, link
from adminfilters.value import ValueFilter
from django.contrib.admin import register
from django.core.cache import caches
from django.urls import NoReverseMatch
from smart_admin.modeladmin import SmartModelAdmin

from ...administration.mixin import LoadDumpMixin
from ..admin_sync import SyncMixin
from ..models import OptionSet
from ..utils import render
from .base import ConcurrencyVersionAdmin

logger = logging.getLogger(__name__)

cache = caches["default"]


@register(OptionSet)
class OptionSetAdmin(LoadDumpMixin, SyncMixin, ConcurrencyVersionAdmin, SmartModelAdmin):
    list_display = (
        "name",
        "id",
        "separator",
        "comment",
        "pk_col",
    )
    search_fields = ("name",)
    list_filter = (("data", ValueFilter.factory(lookup_name="icontains")),)
    save_as = True
    readonly_fields = ("version", "last_update_date")
    object_history_template = "reversion-compare/object_history.html"
    exclude = ("columns",)

    @button()
    def display_data(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Data")
        obj: OptionSet = ctx["original"]
        data = []
        for line in obj.data.split("\r\n"):
            data.append(line.split(obj.separator))
        ctx["data"] = data
        return render(request, "admin/core/optionset/table.html", ctx)

    @link(change_form=True, change_list=False, html_attrs={"target": "_new"})
    def view_json(self, button):
        original = button.context["original"]
        if original:
            try:
                button.href = original.get_api_url()
            except NoReverseMatch:
                button.href = "#"
                button.label = "Error reversing url"

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.method == "POST" and "_saveasnew" in request.POST:
            object_id = None

        return super().change_view(request, object_id)
