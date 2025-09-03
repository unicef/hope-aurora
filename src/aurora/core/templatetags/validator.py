import logging
from typing import TYPE_CHECKING

from django.template import Library

if TYPE_CHECKING:
    from aurora.core.models import Validator

logger = logging.getLogger(__name__)
register = Library()


@register.simple_tag()
def validator_error(validator: "Validator") -> str:
    return ""


@register.simple_tag()
def validator_status(validator: "Validator") -> str:
    return ""
