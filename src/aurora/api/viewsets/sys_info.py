import os

from constance import config
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView

from aurora.core.utils import has_token, is_root


class IsRootUser(BasePermission):
    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and is_root(request))


class SystemInfoView(APIView):
    permission_classes = (IsRootUser,)

    def get(self, request: HttpRequest) -> JsonResponse:
        data = {
            "build_date": os.environ.get("BUILD_DATE", ""),
            "version": os.environ.get("VERSION", ""),
            "debug": settings.DEBUG,
            "env": settings.SMART_ADMIN_HEADER,
            "sentry_dsn": settings.SENTRY_DSN,
            "cache": config.CACHE_VERSION,
            "has_token": has_token(request),
        }
        return JsonResponse(data)
