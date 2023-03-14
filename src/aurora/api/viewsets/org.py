from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ...core.models import Organization, Project
from ..serializers import OrganizationSerializer, ProjectSerializer
from .base import SmartViewSet


class OrganizationViewSet(SmartViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    # lookup_field = "slug"

    @action(detail=True, methods=["GET"])
    def projects(self, request, pk=None):
        # item = Organization.objects.get(slug=slug)
        queryset = Project.objects.filter(organization__id=pk)
        serializer = ProjectSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
