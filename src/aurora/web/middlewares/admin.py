import logging
import re
from typing import TYPE_CHECKING, Callable
from urllib.parse import urlparse

from constance import config
from django.conf import settings
from django.http import HttpResponse
if TYPE_CHECKING:
    from django.http import HttpRequest


logger = logging.getLogger(__name__)


def is_admin_site(request: "HttpRequest") -> bool:
    parts = urlparse(request.build_absolute_uri())
    return bool(re.compile(config.WAF_ADMIN_ALLOWED_HOSTNAMES).match(parts.netloc))


def is_public_site(request: "HttpRequest") -> bool:
    parts = urlparse(request.build_absolute_uri())
    return bool(re.compile(config.WAF_REGISTRATION_ALLOWED_HOSTNAMES).match(parts.netloc))


class AdminSiteMiddleware:
    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: "HttpRequest") -> "HttpResponse":
        if config.WAF_REGISTRATION_ALLOWED_HOSTNAMES:
            parts = urlparse(request.build_absolute_uri())
            try:
                if parts.path.startswith(f"/{settings.DJANGO_ADMIN_URL}") and not is_admin_site(request):
                    return HttpResponse("Not Allowed")
                if not is_public_site(request):
                    return HttpResponse("Not Allowed")
            except Exception as e:
                logging.exception(e)
        return self.get_response(request)
