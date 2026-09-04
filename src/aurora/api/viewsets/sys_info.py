import os
from typing import TYPE_CHECKING

from constance import config
from django.conf import settings
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from aurora.core.utils import has_token

if TYPE_CHECKING:
    from rest_framework.request import Request


class StaffOnly(BasePermission):
    message = "Only staff users can access this endpoint."

    def has_permission(self, request: "Request", view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class SystemInfo(APIView):
    permission_classes = [IsAuthenticated, StaffOnly]

    def get(self, request: "Request") -> Response:
        data = {
            "build_date": os.environ.get("BUILD_DATE", ""),
            "version": os.environ.get("VERSION", ""),
            "debug": settings.DEBUG,
            "env": settings.SMART_ADMIN_HEADER,
            "sentry_dsn": settings.SENTRY_DSN,
            "cache": config.CACHE_VERSION,
            "has_token": has_token(request),
        }
        return Response(data)


system_info = SystemInfo.as_view()
