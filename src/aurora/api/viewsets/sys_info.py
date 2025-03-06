import os

from constance import config
from django.conf import settings
from django.http import JsonResponse

from aurora.core.utils import has_token


def system_info(request):
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
