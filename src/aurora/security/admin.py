import logging

from admin_extra_buttons.decorators import button
from admin_sync.exceptions import SyncError
from admin_sync.protocol import LoadDumpProtocol
from adminactions.helpers import AdminActionPermMixin
from adminfilters.autocomplete import AutoCompleteFilter
from django.utils.translation import gettext_lazy as _
from hijack.templatetags.hijack import can_hijack
from smart_admin.modeladmin import SmartModelAdmin
from smart_admin.smart_auth.admin import GroupAdmin as GroupAdmin_
from smart_admin.smart_auth.admin import UserAdmin as UserAdmin_

from aurora.administration.hijack import impersonate
from aurora.core.admin_sync import SyncMixin
from aurora.core.utils import is_root

from .ad import ADUSerMixin
from .forms import AuroraRoleForm

logger = logging.getLogger(__name__)


class GroupProtocol(LoadDumpProtocol):
    def collect(self, data):
        from django.contrib.auth.models import Group

        if len(data) == 0:
            raise SyncError("Empty queryset")  # pragma: no cover

        if not isinstance(data[0], Group):  # pragma: no cover
            raise ValueError("GroupProtocol can be used only for Registration")
        return list(data)


class GroupAdmin(AdminActionPermMixin, SyncMixin, GroupAdmin_):
    protocol_class = GroupProtocol


class UserAdmin(AdminActionPermMixin, ADUSerMixin, UserAdmin_):
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


class UserProfileAdmin(SmartModelAdmin):
    search_fields = ("user__username",)
    list_display = ("user", "job_title")
    raw_id_fields = ("user",)


class AuroraRoleAdmin(SyncMixin, SmartModelAdmin):
    list_display = ("organization", "project", "registration", "user", "role")
    list_filter = (
        ("organization", AutoCompleteFilter),
        ("project", AutoCompleteFilter),
        ("registration", AutoCompleteFilter),
        ("user", AutoCompleteFilter),
        ("role", AutoCompleteFilter),
    )
    autocomplete_fields = ("registration", "user", "role")
    form = AuroraRoleForm
    fieldsets = (
        (None, {"fields": ("user", "role")}),
        (_("Scope"), {"fields": ("organization", "project", "registration")}),
        (
            _("Validity"),
            {
                "fields": (
                    "valid_from",
                    "valid_until",
                ),
            },
        ),
    )


#
# @register(RegistrationRole)
# class RegistrationRoleAdmin(SyncMixin, SmartModelAdmin):
#     list_display = ("registration", "user", "role")
#     list_filter = (
#         ("registration", AutoCompleteFilter),
#         ("user", AutoCompleteFilter),
#         ("role", AutoCompleteFilter),
#     )
#     autocomplete_fields = ("registration", "user", "role")
#
#
# @register(OrganizationRole)
# class OrganizationRoleAdmin(SyncMixin, SmartModelAdmin):
#     list_display = ("organization", "user", "role")
#     list_filter = (
#         ("organization", AutoCompleteFilter),
#         ("user", AutoCompleteFilter),
#         ("role", AutoCompleteFilter),
#     )
