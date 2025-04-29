import logging
from typing import TYPE_CHECKING

from adminfilters.autocomplete import AutoCompleteFilter
from adminfilters.combo import ChoicesFieldComboFilter, RelatedFieldComboFilter
from django.contrib.admin.options import IncorrectLookupParameters
from django.core.cache import caches
from django.core.exceptions import ValidationError
from django.db.models import Q, QuerySet
from django.urls import reverse
from strategy_field.admin import StrategyFieldListFilter

if TYPE_CHECKING:
    from django.http import HttpRequest


logger = logging.getLogger(__name__)

cache = caches["default"]


class Select2FieldComboFilter(ChoicesFieldComboFilter):
    template = "adminfilters/select2.html"


class StrategyFieldSelect2Filter(Select2FieldComboFilter, StrategyFieldListFilter):
    pass


class Select2RelatedFieldComboFilter(RelatedFieldComboFilter):
    template = "adminfilters/select2.html"


class ProjectFilter(AutoCompleteFilter):
    fk_name = "project__organization__exact"

    def __init__(self, field, request, params, model, model_admin, field_path):  # noqa
        self.request = request
        super().__init__(field, request, params, model, model_admin, field_path)

    def has_output(self) -> bool:
        return "project__organization__exact" in self.request.GET

    def get_url(self) -> str:
        url = reverse("%s:autocomplete" % self.admin_site.name)
        if self.fk_name in self.request.GET:
            oid = self.request.GET[self.fk_name]
            return f"{url}?oid={oid}"
        return url


class UsedByRegistration(AutoCompleteFilter):
    def has_output(self) -> bool:
        return "project__exact" in self.request.GET

    def queryset(self, request: "HttpRequest", queryset: QuerySet) -> "QuerySet":
        if not self.used_parameters:
            return queryset
        try:
            value = self.used_parameters["registration__exact"]
            return queryset.filter(Q(registration__exact=value) | Q(formset__parent__registration=value))
        except (ValueError, ValidationError) as e:
            # Fields may raise a ValueError or ValidationError when converting
            # the parameters to the correct type.
            raise IncorrectLookupParameters(e) from e


class UsedInRFormset(AutoCompleteFilter):
    def has_output(self) -> bool:
        return "project__exact" in self.request.GET
