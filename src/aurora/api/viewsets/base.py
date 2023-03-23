from django_filters import rest_framework as filters
from django_filters import utils
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import BasePermission, DjangoModelPermissions

from aurora.core.models import (
    CustomFieldType,
    FlexForm,
    FlexFormField,
    OptionSet,
    Organization,
    Project,
    Validator,
)
from aurora.core.utils import is_root
from aurora.registration.models import Record, Registration
from dbtemplates.models import Template


class LastModifiedFilter(filters.FilterSet):
    modified_after = filters.DateFilter(label="Updated after", field_name="last_update_date", lookup_expr="gte")
    # date_range = filters.DateFromToRangeFilter(widget=RangeWidget(attrs={'placeholder': 'YYYY/MM/DD'}))


class IsRootUser(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and is_root(request))


class AuroraPermission(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and is_root(request))

    def has_object_permission(self, request, view, obj):
        return True


class AuroraFilterBackend(DjangoFilterBackend):
    MAP = {
        Organization: None,
        Project: None,
        Registration: None,
        Validator: None,
        FlexForm: None,
        FlexFormField: None,
        OptionSet: None,
        CustomFieldType: None,
        Template: None,
        Record: None,
    }

    def filter_queryset(self, request, queryset, view):
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        if not filterset.is_valid() and self.raise_exception:
            raise utils.translate_validation(filterset.errors)
        return filterset.qs


class SmartViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (SessionAuthentication, TokenAuthentication, BasicAuthentication)
    permission_classes = (IsRootUser | AuroraPermission | DjangoModelPermissions,)
    filter_backends = [AuroraFilterBackend]
    filterset_class = LastModifiedFilter
