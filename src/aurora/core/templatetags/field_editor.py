import logging
from typing import Any

from django.forms import BoundField, Form
from django.template import Library

logger = logging.getLogger(__name__)
register = Library()


@register.filter()
def field(form: Form, field_name: str) -> BoundField:
    return form[field_name]


@register.filter()
def get(d: dict, key: str) -> Any:
    return d[key]
