import json
import logging

from django.core.cache import cache
from django.template import Library

from aurora.state import state

logger = logging.getLogger(__name__)
register = Library()


@register.simple_tag()
def validator_error(validator):
    return ""


@register.simple_tag()
def validator_status(validator):
    return ""
