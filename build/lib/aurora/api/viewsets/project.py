from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ...core.models import Project
from ...registration.models import Registration
from ..serializers import ProjectSerializer, RegistrationListSerializer
from .base import SmartViewSet


class ProjectViewSet(SmartViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=["GET"])
    def registrations(self, request, pk=None):
        queryset = Registration.objects.filter(project__id=pk)
        serializer = RegistrationListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
