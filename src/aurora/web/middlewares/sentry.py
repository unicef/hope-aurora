import logging
import os
from typing import TYPE_CHECKING, Callable

from django.conf import settings
from sentry_sdk import configure_scope

if TYPE_CHECKING:
    from django.http import HttpRequest, HttpResponse


logger = logging.getLogger(__name__)


class SentryMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: "HttpRequest") -> "HttpResponse":
        with configure_scope() as scope:
            scope.set_tag("debug", settings.DEBUG)
            scope.set_tag("Version", os.environ.get("VERSION", "?"))
            scope.set_tag("Build", os.environ.get("BUILD_DATE", "?"))
            return self.get_response(request)
