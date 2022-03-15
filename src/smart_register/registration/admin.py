from admin_extra_buttons.decorators import view, link
from adminfilters.autocomplete import AutoCompleteFilter
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from import_export import resources

from django.contrib.admin import register
from import_export.admin import ImportExportMixin
from smart_admin.modeladmin import SmartModelAdmin

from .models import Registration, Record


class RegistrationResource(resources.ModelResource):
    class Meta:
        model = Registration


@register(Registration)
class RegistrationAdmin(ImportExportMixin, SmartModelAdmin):
    search_fields = ("name",)
    date_hierarchy = "start"
    list_filter = ("active",)
    list_display = ("name", "start", "end", "active", "locale", "secure")
    exclude = ("public_key",)
    change_form_template = None
    autocomplete_fields = ("flex_form",)
    save_as = True

    def secure(self, obj):
        return bool(obj.public_key)

    secure.boolean = True

    @link(html_attrs={"class": "aeb-green "})
    def _view_on_site(self, button):
        button.href = reverse("register", args=[button.original.pk])
        button.html_attrs["target"] = f"_{button.original.pk}"

    @view()
    def removekey(self, request, pk):
        self.object = self.get_object(request, pk)
        self.object.public_key = ""
        self.object.save()
        self.message_user(request, "Encryption key removed", messages.WARNING)

    @view()
    def generate_keys(self, request, pk):
        ctx = self.get_common_context(
            request, pk, title="Generate Private/Public Key pair to encrypt this Registration data"
        )

        if request.method == "POST":
            ctx["title"] = "Key Pair Generated"
            private_pem, public_pem = self.object.setup_encryption_keys()
            ctx["private_key"] = private_pem
            ctx["public_key"] = public_pem

        return render(request, "admin/registration/registration/keys.html", ctx)


@register(Record)
class RecordAdmin(SmartModelAdmin):
    date_hierarchy = "timestamp"
    search_fields = ("registration__name",)
    list_display = ("registration", "timestamp", "id")
    readonly_fields = ("registration", "timestamp", "id")
    list_filter = (("registration", AutoCompleteFilter),)
    change_form_template = None
