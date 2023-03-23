import logging
import os

from django.conf import settings
from sentry_sdk import configure_scope

logger = logging.getLogger(__name__)


class SentryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        with configure_scope() as scope:
            scope.set_tag("debug", settings.DEBUG)
            scope.set_tag("Version", os.environ.get("VERSION", "?"))
            scope.set_tag("Build", os.environ.get("BUILD_DATE", "?"))
            response = self.get_response(request)
        return response
