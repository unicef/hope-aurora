from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from ...core.models import Organization, Project
from ..serializers import OrganizationSerializer, ProjectSerializer
from .base import AuroraScopeFilterBackend, SmartViewSet


class OrganizationViewSet(SmartViewSet):
    queryset = Organization.objects.order_by("lft")
    serializer_class = OrganizationSerializer

    @action(detail=True, methods=["GET"])
    def projects(self, request: Request, pk: str | None = None) -> Response:
        self.get_object()
        queryset = AuroraScopeFilterBackend().filter_queryset(
            request, Project.objects.filter(organization__id=pk), self
        )
        page = self.paginate_queryset(queryset)

        serializer = ProjectSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
