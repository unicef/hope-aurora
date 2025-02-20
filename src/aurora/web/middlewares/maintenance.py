import logging

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from constance import config

from aurora.core.utils import has_token

logger = logging.getLogger(__name__)


class MaintenanceMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """Code to be executed for each request before the view (and later middleware) are called."""
        if config.MAINTENANCE_MODE:
            url = reverse("maintenance")
            if not (url == request.path or settings.DJANGO_ADMIN_URL in request.path or has_token(request)):
                return HttpResponseRedirect(url)

        return self.get_response(request)
