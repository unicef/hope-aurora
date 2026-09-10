from typing import TYPE_CHECKING, cast

from django.db.models import QuerySet
from django.http import HttpRequest
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ...core.models import Project
from ...registration.models import Registration
from ..serializers import ProjectSerializer, RegistrationListSerializer
from .base import SmartViewSet

if TYPE_CHECKING:
    from ...security.models import User


class ProjectViewSet(SmartViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def scope_queryset(self, qs: QuerySet[Project], user: "User") -> QuerySet[Project]:
        return qs.filter(pk__in=user.accessible_project_ids)

    @action(detail=True, methods=["GET"])
    def registrations(self, request: HttpRequest, pk: str | None = None) -> Response:
        queryset = Registration.objects.filter(project__id=pk)
        if not getattr(request.user, "is_superuser", False):
            queryset = queryset.filter(pk__in=cast("User", request.user).accessible_registration_ids)
        serializer = RegistrationListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
