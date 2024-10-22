import logging
import re
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse

from constance import config

logger = logging.getLogger(__name__)


def is_admin_site(request):
    parts = urlparse(request.build_absolute_uri())
    return re.compile(config.WAF_ADMIN_ALLOWED_HOSTNAMES).match(parts.netloc)


def is_public_site(request):
    parts = urlparse(request.build_absolute_uri())
    return re.compile(config.WAF_REGISTRATION_ALLOWED_HOSTNAMES).match(parts.netloc)


class AdminSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if config.WAF_REGISTRATION_ALLOWED_HOSTNAMES:
            parts = urlparse(request.build_absolute_uri())
            try:
                if parts.path.startswith(f"/{settings.DJANGO_ADMIN_URL}"):
                    if not is_admin_site(request):
                        return HttpResponse("Not Allowed")
                else:
                    if not is_public_site(request):
                        return HttpResponse("Not Allowed")
            except Exception as e:
                logging.exception(e)
            ret = self.get_response(request)
            return ret
        else:
            return self.get_response(request)
