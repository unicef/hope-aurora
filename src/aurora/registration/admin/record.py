import json
import logging

from admin_extra_buttons.decorators import button, link
from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.numbers import NumberFilter
from adminfilters.value import ValueFilter
from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from smart_admin.modeladmin import SmartModelAdmin

from ...core.utils import is_root
from ..forms import DecryptForm
from .filters import DateRangeFilter, HourFilter
from .paginator import LargeTablePaginator

logger = logging.getLogger(__name__)


class RecordAdmin(SmartModelAdmin):
    search_fields = ("registration__name",)
    list_display = ("timestamp", "remote_ip", "id", "registration", "ignored")
    readonly_fields = ("registration", "timestamp", "remote_ip", "id", "fields", "counters")
    list_filter = (
        ("registration", AutoCompleteFilter),
        ("registrar", AutoCompleteFilter),
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

    def get_actions(self, request):
        return {}
        # {name: (func, name, desc) for func, name, desc in actions}
        # actions = super().get_actions(request)
        # for name, __ in actions.items():
        #     print("src/aurora/registration/admin.py: 485", name)
        # return {"export_as_csv": self.get_action(self.export_as_csv)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        qs = qs.select_related("registration", "registrar")
        return qs

    def get_common_context(self, request, pk=None, **kwargs):
        return super().get_common_context(request, pk, is_root=is_root(request), **kwargs)

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        extra_context = {"is_root": is_root(request)}
        return super().changeform_view(request, object_id, form_url, extra_context)

    @link(html_attrs={"class": "aeb-warn "}, change_form=True)
    def receipt(self, button):
        try:
            if button.original:
                base = reverse("register-done", args=[button.original.registration.pk, button.original.pk])
                button.href = base
                button.html_attrs["target"] = f"_{button.original.pk}"
        except Exception as e:
            logger.exception(e)

    @button(label="Preview", permission=is_root)
    def preview(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Preview")

        return render(request, "admin/registration/record/preview.html", ctx)

    @button(label="inspect", permission=is_root)
    def inspect(self, request, pk):
        ctx = self.get_common_context(request, pk, title="Inspect")
        ctx["files_as_dict"] = json.loads(self.object.files.tobytes().decode())
        return render(request, "admin/registration/record/inspect.html", ctx)

    @button(permission=is_root)
    def decrypt(self, request, pk):
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

    def get_readonly_fields(self, request, obj=None):
        if is_root(request) or settings.DEBUG:
            return []
        return self.readonly_fields

    def has_view_permission(self, request, obj=None):
        return is_root(request) or settings.DEBUG

    def has_add_permission(self, request):
        return is_root(request) or settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG

    def has_change_permission(self, request, obj=None):
        return is_root(request) or settings.DEBUG
