from rest_framework.decorators import action

from ...core.models import Organization, Project
from ..serializers import OrganizationSerializer, ProjectSerializer
from .base import SmartViewSet


class OrganizationViewSet(SmartViewSet):
    queryset = Organization.objects.order_by("lft")
    serializer_class = OrganizationSerializer

    @action(detail=True, methods=["GET"])
    def projects(self, request, pk=None):
        queryset = Project.objects.filter(organization__id=pk)
        page = self.paginate_queryset(queryset)

        serializer = ProjectSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)
