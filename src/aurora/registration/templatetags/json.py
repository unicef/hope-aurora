import json
import logging
from typing import Dict

from django.template import Library
from django.utils.safestring import mark_safe
from pygments import highlight, lexers
from pygments.formatters import HtmlFormatter

logger = logging.getLogger(__name__)
register = Library()


@register.filter
def pretty_json(json_object: Dict) -> str:
    json_str = json.dumps(json_object, indent=4, sort_keys=True)
    lex = lexers.get_lexer_by_name("json")
    return mark_safe(highlight(json_str, lex, HtmlFormatter()))
