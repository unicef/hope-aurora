import logging

from admin_extra_buttons.decorators import button
from adminactions.helpers import AdminActionPermMixin
from adminfilters.autocomplete import AutoCompleteFilter
from django.contrib.admin import register
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from hijack.templatetags.hijack import can_hijack
from smart_admin.decorators import smart_register
from smart_admin.modeladmin import SmartModelAdmin
from smart_admin.smart_auth.admin import GroupAdmin
from smart_admin.smart_auth.admin import UserAdmin as UserAdmin_

from aurora.administration.hijack import impersonate
from aurora.core.admin_sync import SyncMixin
from aurora.core.utils import is_root

from .models import OrganizationRole, RegistrationRole, UserProfile

logger = logging.getLogger(__name__)


@smart_register(User)
class UserAdmin(AdminActionPermMixin, UserAdmin_):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_superuser")
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


class AuroraGroupAdmin(AdminActionPermMixin, SyncMixin, GroupAdmin):
    pass


@smart_register(UserProfile)
class UserProfileAdmin(SmartModelAdmin):
    pass


@register(RegistrationRole)
class RegistrationRoleAdmin(SyncMixin, SmartModelAdmin):
    list_display = ("registration", "user", "role")
    list_filter = (
        ("registration", AutoCompleteFilter),
        ("user", AutoCompleteFilter),
        ("role", AutoCompleteFilter),
    )
    autocomplete_fields = ("registration", "user", "role")


@register(OrganizationRole)
class OrganizationRoleAdmin(SyncMixin, SmartModelAdmin):
    list_display = ("organization", "user", "role")
    list_filter = (
        ("organization", AutoCompleteFilter),
        ("user", AutoCompleteFilter),
        ("role", AutoCompleteFilter),
    )
