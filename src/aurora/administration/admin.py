from admin_extra_buttons.decorators import button
from adminactions.helpers import AdminActionPermMixin
from django.utils.translation import gettext_lazy as _
from hijack.templatetags.hijack import can_hijack
from smart_admin.smart_auth.admin import GroupAdmin, UserAdmin

from aurora.administration.hijack import impersonate
from aurora.core.admin_sync import SyncMixin
from aurora.core.utils import is_root


class AuroraUserAdmin(AdminActionPermMixin, UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    @button(permission=lambda req, obj, **kw: is_root(req) and can_hijack(req.user, obj))
    def hijack(self, request, pk):
        hijacked = self.get_object(request, pk)
        impersonate(request, hijacked)


class AuroraUserAdminTemp(AuroraUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_superuser", "user")

    def get_list_display(self, request):
        return super().get_list_display(request)


class AuroraGroupAdmin(AdminActionPermMixin, SyncMixin, GroupAdmin):
    pass
