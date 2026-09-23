from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from ...core.models import Project
from ...registration.models import Registration
from ..serializers import ProjectSerializer, RegistrationListSerializer
from .base import AuroraScopeFilterBackend, SmartViewSet


class ProjectViewSet(SmartViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    @action(detail=True, methods=["GET"])
    def registrations(self, request: Request, pk: str | None = None) -> Response:
        self.get_object()
        queryset = AuroraScopeFilterBackend().filter_queryset(
            request, Registration.objects.filter(project__id=pk), self
        )
        serializer = RegistrationListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
