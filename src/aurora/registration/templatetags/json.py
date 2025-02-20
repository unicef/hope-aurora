import json
import logging

from django.template import Library

from pygments import highlight, lexers
from pygments.formatters import HtmlFormatter

logger = logging.getLogger(__name__)
register = Library()


@register.filter
def pretty_json(json_object: dict) -> str:
    json_str = json.dumps(json_object, indent=4, sort_keys=True)
    lex = lexers.get_lexer_by_name("json")
    return highlight(json_str, lex, HtmlFormatter())
