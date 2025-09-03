import logging
import re
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from adminfilters.filters import AutoCompleteFilter, NumberFilter
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.urls import reverse
from django.utils.translation import gettext as _

from aurora.core.admin.filters import ProjectFilter

if TYPE_CHECKING:
    from django.contrib.admin import ModelAdmin
    from django.db.models import QuerySet
    from django.http import HttpRequest

logger = logging.getLogger(__name__)


class OrganizationFilter(AutoCompleteFilter):
    pass


class RegistrationProjectFilter(ProjectFilter):
    pass


class HourFilter(SimpleListFilter):
    parameter_name = "hours"
    title = "Latest [n] hours"
    slots = (
        (30, _("30 min")),
        (60, _("1 hour")),
        (60 * 4, _("4 hour")),
        (60 * 6, _("6 hour")),
        (60 * 8, _("8 hour")),
        (60 * 12, _("12 hour")),
        (60 * 24, _("24 hour")),
    )

    def lookups(self, request: "HttpRequest", model_admin: "ModelAdmin") -> tuple[tuple[int, str], ...]:
        return self.slots

    def queryset(self, request: "HttpRequest", queryset: "QuerySet") -> "QuerySet":
        if self.value():
            offset = datetime.now() - timedelta(minutes=int(self.value()))
            queryset = queryset.filter(timestamp__gte=offset)

        return queryset
