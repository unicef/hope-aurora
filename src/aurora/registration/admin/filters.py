import logging
import re
from datetime import datetime, timedelta

from adminfilters.numbers import NumberFilter
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.urls import reverse
from django.utils.translation import gettext as _

from ...administration.filters import BaseAutoCompleteFilter

logger = logging.getLogger(__name__)


class OrganizationFilter(BaseAutoCompleteFilter):
    pass


class RegistrationProjectFilter(BaseAutoCompleteFilter):
    fk_name = "flex_form__project__organization__exact"

    def has_output(self):
        return "flex_form__project__organization__exact" in self.request.GET

    def get_url(self):
        url = reverse("%s:autocomplete" % self.admin_site.name)
        if self.fk_name in self.request.GET:
            oid = self.request.GET[self.fk_name]
            return f"{url}?oid={oid}"
        return url


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

    def lookups(self, request, model_admin):
        return self.slots

    def queryset(self, request, queryset):
        if self.value():
            offset = datetime.now() - timedelta(minutes=int(self.value()))
            queryset = queryset.filter(timestamp__gte=offset)

        return queryset


class DateRangeFilter(NumberFilter):
    rex1 = re.compile(r"^(>=|<=|>|<|=)?(\d{4}-\d{2}-\d{2})$")
    re_range = re.compile(r"^(\d{4}-\d{2}-\d{2})..(\d{4}-\d{2}-\d{2})$")
    re_list = re.compile(r"(\d{4}-\d{2}-\d{2}),?")
    re_unlike = re.compile(r"^(<>)(?P<date>\d{4}-\d{2}-\d{2})$")

    def queryset(self, request, queryset):
        if self.value() and self.value()[0]:
            raw_value = self.value()[0]
            m1 = self.rex1.match(raw_value)
            m_range = self.re_range.match(raw_value)
            m_list = self.re_list.match(raw_value)
            m_unlike = self.re_unlike.match(raw_value)
            if m_unlike and m_unlike.groups():
                match = "%s__date__exact" % self.field.name
                op, value = self.re_unlike.match(raw_value).groups()
                queryset = queryset.exclude(**{match: value})
            else:
                if m1 and m1.groups():
                    op, value = self.rex1.match(raw_value).groups()
                    match = "%s__date__%s" % (self.field.name, self.map[op or "="])
                    self.filters = {match: value}
                elif m_range and m_range.groups():
                    start, end = self.re_range.match(raw_value).groups()
                    self.filters = {f"{self.field.name}__date__gte": start, f"{self.field.name}__date__lte": end}
                elif m_list and m_list.groups():
                    value = raw_value.split(",")
                    match = "%s__date__in" % self.field.name
                    self.filters = {match: value}
                # elif m_unlike and m_unlike.groups():
                #     match = '%s__exact' % self.field.name
                #     op, value = self.re_unlike.match(raw).groups()
                #     queryset = queryset.exclude(**{match: value})
                else:  # pragma: no cover
                    raise IncorrectLookupParameters()
                try:
                    queryset = queryset.filter(**self.filters)
                except Exception:
                    raise IncorrectLookupParameters(self.value())
        return queryset
