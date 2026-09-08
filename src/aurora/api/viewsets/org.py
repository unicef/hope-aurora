from typing import TYPE_CHECKING, cast

from django.db.models import QuerySet
from django.http import HttpRequest
from rest_framework.decorators import action
from rest_framework.response import Response

from ...core.models import Organization, Project
from ..serializers import OrganizationSerializer, ProjectSerializer
from .base import SmartViewSet

if TYPE_CHECKING:
    from ...security.models import User


class OrganizationViewSet(SmartViewSet):
    queryset = Organization.objects.order_by("lft")
    serializer_class = OrganizationSerializer

    def scope_queryset(self, qs: QuerySet[Organization], user: "User") -> QuerySet[Organization]:
        return qs.filter(pk__in=user.accessible_organization_ids)

    @action(detail=True, methods=["GET"])
    def projects(self, request: HttpRequest, pk: str | None = None) -> Response:
        queryset = Project.objects.filter(organization__id=pk)
        if not getattr(request.user, "is_superuser", False):
            queryset = queryset.filter(pk__in=cast("User", request.user).accessible_project_ids)
        page = self.paginate_queryset(queryset)

        serializer = ProjectSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
