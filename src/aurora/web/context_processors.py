import os
from typing import TYPE_CHECKING, Any

from django.conf import settings

from aurora import __version__
from aurora.core.utils import get_session_id, has_token, is_root

if TYPE_CHECKING:
    from django.http import HttpRequest


def smart(request: "HttpRequest") -> dict[str, Any]:
    return {
        "session_id": get_session_id(),
        "user_is_root": is_root(request),
        "user_has_token": has_token(request),
        "project": {
            "build_date": os.environ.get("BUILD_DATE", "no date"),
            "version": __version__,
            "commit": os.environ.get("GIT_SHA", "<dev>")[:8],
            "debug": settings.DEBUG,
            "env": settings.SMART_ADMIN_HEADER,
            "sentry_dsn": settings.SENTRY_DSN,
            "has_token": has_token(request),
            "languages": settings.LANGUAGES,
            "settings": settings,
        },
    }
