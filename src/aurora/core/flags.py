from django.conf import settings
from django.core.exceptions import ValidationError

from adminactions.utils import get_attr
from flags import conditions
from flags.conditions import validate_parameter

from aurora.core.utils import get_client_ip


def parse_bool(value):
    return str(value).upper() in ["1", "Y", "YES", "T", "TRUE", "ON"]


def validate_bool(value):
    if value not in ["true", "false"]:
        raise ValidationError("Enter true/false")


@conditions.register("debug")
def debug(param, *args, **kwargs):
    return settings.DEBUG is parse_bool(param)


@conditions.register("localhost")
def localhost(path, request=None, **kwargs):
    return request.get_host() in ["127.0.0.1", "localhost"]  # noqa: E713


@conditions.register("user field")
def user_field(param_name, request=None, **kwargs):
    try:
        param, value = param_name.split("=")
        return str(get_attr(request.user, param, None)) == value
    except ValueError:
        return False


@conditions.register("client IP")
def client_ip(param_name, request=None, **kwargs):
    return get_client_ip(request) == param_name


@conditions.register("request HEADER", validator=validate_parameter)
def request_header(param_name, request=None, **kwargs):
    try:
        param, value = param_name.split("=")
    except ValueError:
        param = param_name
        value = ""
    key = f"HTTP_{param.replace('-', '_')}"
    if value:
        enabled = request.META.get(key, None) == value
    else:
        enabled = key in request.META
    return enabled


@conditions.register("Cookie", validator=validate_parameter)
def cookie(param_name, request=None, **kwargs):
    try:
        param, value = param_name.split("=")
    except ValueError:
        param = param_name
        value = ""
    if value:
        enabled = request.COOKIES.get(param)
    else:
        enabled = request.COOKIES.get(param) == value
    return enabled
