from typing import TypeVar

from django.db.models import Model, QuerySet
from django.http import HttpRequest
from django_filters import rest_framework as filters
from django_filters import utils
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.filters import BaseFilterBackend
from rest_framework.permissions import AllowAny, BasePermission, DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.views import APIView

from aurora.core.models import (
    FlexForm,
    FlexFormField,
    FormSet,
    Organization,
    Project,
)
from aurora.core.utils import is_root
from aurora.counters.models import Counter
from aurora.registration.models import Record, Registration
from aurora.security.scope import get_role_scope

_Model = TypeVar("_Model", bound=Model)
_Row = TypeVar("_Row", default=_Model)


class LastModifiedFilter(filters.FilterSet):
    modified_after = filters.DateFilter(label="Updated after", field_name="last_update_date", lookup_expr="gte")


class IsRootUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and is_root(request))


class AuroraPermission(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and is_root(request))

    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        return True


class AuroraFilterBackend(DjangoFilterBackend):
    def filter_queryset(self, request: HttpRequest, queryset: QuerySet[Model], view: APIView) -> QuerySet[Model]:
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        if not filterset.is_valid() and self.raise_exception:
            raise utils.translate_validation(filterset.errors)
        return filterset.qs


class AuroraScopeFilterBackend(BaseFilterBackend):
    """Restrict results to the part of the hierarchy the requesting user holds a role in.

    Model permissions establish that a user may read a given kind of record; they say nothing about
    whose records. Models absent from PATHS are shared reference data with no owning organization
    (validators, option sets, field types, templates, flat pages) and stay readable.
    """

    # model -> lookup path from that model to the organization, project and registration it belongs to.
    # Organizations and projects also resolve downwards, so that a role on a single registration still
    # reveals the project and organization containing it and the hierarchy stays navigable.
    PATHS: dict[type[Model], tuple[str, str | None, str | None]] = {
        Organization: ("pk", "projects", "projects__registrations"),
        Project: ("organization", "pk", "registrations"),
        Registration: ("project__organization", "project", "pk"),
        Record: ("registration__project__organization", "registration__project", "registration"),
        Counter: ("registration__project__organization", "registration__project", "registration"),
        FlexForm: ("project__organization", "project", "registration"),
        FormSet: ("parent__project__organization", "parent__project", "parent__registration"),
        FlexFormField: ("flex_form__project__organization", "flex_form__project", "flex_form__registration"),
    }

    def filter_queryset(
        self, request: Request, queryset: QuerySet[_Model, _Row], view: APIView
    ) -> QuerySet[_Model, _Row]:
        paths = self.PATHS.get(queryset.model)
        if paths is None or self.is_public(view):
            return queryset
        scope = get_role_scope(request.user)
        if scope.unlimited:
            return queryset
        return queryset.filter(scope.as_q(*paths)).distinct()

    @staticmethod
    def is_public(view: APIView) -> bool:
        """Registration metadata and version are served to anonymous applicants by design."""
        return AllowAny in getattr(view, "permission_classes", ())


class SmartViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (
        SessionAuthentication,
        TokenAuthentication,
        BasicAuthentication,
    )
    permission_classes = (IsRootUser | AuroraPermission | DjangoModelPermissions,)
    filter_backends = [AuroraFilterBackend, AuroraScopeFilterBackend]
    filterset_class = LastModifiedFilter
