from typing import TYPE_CHECKING, Any, cast

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
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

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
from aurora.security.models import User
from dbtemplates.models import Template

if TYPE_CHECKING:
    from rest_framework.viewsets import GenericViewSet


class LastModifiedFilter(filters.FilterSet):
    modified_after = filters.DateFilter(label="Updated after", field_name="last_update_date", lookup_expr="gte")


class IsRootUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and is_root(request))


class AuroraPermission(BasePermission):
    """Role-based, scope-aware permission for the API.

    Grants access when the request is made by a root/superuser, or by any
    authenticated user holding at least one currently-valid role assignment.
    Object-level authorization is enforced through scope-filtered querysets
    (see ``SmartViewSet.get_queryset``); ``has_object_permission`` performs an
    explicit scope check as a second line of defense.
    """

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or is_root(request):
            return True
        return user.has_active_role()

    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        user = request.user
        if not (user and user.is_authenticated):
            return False
        if user.is_superuser or is_root(request):
            return True
        generic_view = cast("GenericViewSet", view)
        return generic_view.filter_queryset(generic_view.get_queryset()).filter(pk=obj.pk).exists()


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

    def filter_queryset(self, request: HttpRequest, queryset: QuerySet[Model], view: APIView) -> QuerySet[Model]:
        filterset = self.get_filterset(request, queryset, view)
        if filterset is None:
            return queryset

        if not filterset.is_valid() and self.raise_exception:
            raise utils.translate_validation(filterset.errors)
        return filterset.qs


class SmartViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (
        SessionAuthentication,
        TokenAuthentication,
        BasicAuthentication,
    )
    permission_classes = (AuroraPermission,)
    filter_backends = [AuroraFilterBackend]
    filterset_class = LastModifiedFilter

    def get_queryset(self) -> QuerySet[Model]:
        """Scope the queryset to the resources the requesting user is authorized for.

        Superusers/root see everything; other authenticated users are restricted
        to the organizations, projects and registrations covered by their active
        role assignments.
        """
        qs = super().get_queryset()
        user = self.request.user
        if user.is_superuser or is_root(self.request):
            return qs
        if not isinstance(user, User):
            return qs.none()
        return self.scope_queryset(qs, user)

    def scope_queryset(self, qs: "QuerySet[Any]", user: "User") -> "QuerySet[Any]":
        """Leave the queryset unchanged by default.

        Subclasses operating on models with an organization/project/registration
        relationship should override this to restrict the queryset to the user's
        authorized scope.
        """
        return qs
