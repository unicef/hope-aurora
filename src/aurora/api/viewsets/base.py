from django.db.models import Model, Q, QuerySet
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
from rest_framework.permissions import BasePermission, DjangoModelPermissions
from rest_framework.request import Request
from rest_framework.views import APIView

from aurora.core.models import (
    CustomFieldType,
    FlexForm,
    FlexFormField,
    FormSet,
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


class IsRootUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and is_root(request))


class ScopedPermission(BasePermission):
    """Require authentication and enforce object-level role-based access control.

    Access to individual model objects is delegated to the user's model permissions,
    evaluated through AuroraAuthBackend which enforces AuroraRole scoping
    (organization/project/registration) and temporal validity.
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated)

    def has_object_permission(self, request: Request, view: APIView, obj: Model) -> bool:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False
        if is_root(request):
            return True
        queryset = getattr(view, "queryset", None)
        model = getattr(queryset, "model", None)
        if model is None:
            model = getattr(view, "model", None)
        if model is None:
            model = obj.__class__
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        perm = f"{app_label}.view_{model_name}"
        return user.has_perm(perm, obj)


class StaffOnlyPermission(BasePermission):
    message = "Only staff users can access this endpoint."

    def has_permission(self, request: Request, view: APIView) -> bool:
        user = getattr(request, "user", None)
        return bool(user and user.is_authenticated and (user.is_staff or is_root(request)))


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


class ScopedQuerysetFilter(AuroraFilterBackend):
    """Filter querysets to only the resources the requesting user is authorized to access.

    Root users bypass all scoping. Regular users are limited to objects for which they
    hold an AuroraRole assignment (at organization, project, or registration level).
    """

    def filter_queryset(self, request: HttpRequest, queryset: QuerySet[Model], view: APIView) -> QuerySet[Model]:
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or is_root(request) or user.is_staff:
            return super().filter_queryset(request, queryset, view)

        queryset = self._apply_scope(request, queryset, view)
        return super().filter_queryset(request, queryset, view)

    def _apply_scope(self, request: HttpRequest, queryset: QuerySet[Model], view: APIView) -> QuerySet[Model]:  # noqa: C901
        from django.utils import timezone

        from aurora.security.models import AuroraRole

        model = getattr(queryset, "model", None)
        user = getattr(request, "user", None)
        if not model or not user:
            return queryset.none()

        role_qs = AuroraRole.objects.filter(
            user=user,
            valid_from__lte=timezone.now(),
        ).filter(valid_until__isnull=True) | AuroraRole.objects.filter(
            user=user,
            valid_from__lte=timezone.now(),
            valid_until__gte=timezone.now(),
        )

        def accessible_ids(field: str) -> list[int]:
            return list(role_qs.exclude(**{f"{field}_id": None}).values_list(f"{field}_id", flat=True).distinct())

        def accessible_form_ids() -> QuerySet[Registration]:
            return Registration.objects.filter(pk__in=accessible_ids("registration")).values_list(
                "flex_form_id", flat=True
            )

        plan: dict = {}
        if model is Registration:
            plan = {"pk__in": accessible_ids("registration")}
        elif model is Organization:
            plan = {"pk__in": accessible_ids("organization")}
        elif model is Project:
            plan = {"pk__in": accessible_ids("project")}
        elif model is Record:
            plan = {"registration_id__in": accessible_ids("registration")}
        elif model is FlexForm:
            plan = {"pk__in": accessible_form_ids()}
        elif model is FlexFormField:
            plan = {"flex_form_id__in": accessible_form_ids()}
        elif model is FormSet:
            form_ids = accessible_form_ids()
            variants = queryset.filter(Q(parent_id__in=form_ids) | Q(flex_form_id__in=form_ids))
            plan = {"pk__in": variants.values("pk")}

        if not plan:
            return queryset.none()
        return queryset.filter(**plan)


class SmartViewSet(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (
        SessionAuthentication,
        TokenAuthentication,
        BasicAuthentication,
    )
    permission_classes = (IsRootUser | ScopedPermission | DjangoModelPermissions,)
    filter_backends = [ScopedQuerysetFilter]
    filterset_class = LastModifiedFilter
