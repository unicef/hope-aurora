import os

from constance import config
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from aurora.core.utils import has_token


class SystemInfoView(APIView):
    """Build and environment details.

    Rendered as a DRF view so it inherits the same authentication and permission handling as every
    other endpoint. It was previously a bare Django view, which meant the authentication_classes and
    permission_classes declared on the viewsets never applied to it and it answered anyone who could
    reach the host.
    """

    permission_classes = (IsAuthenticated,)

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
