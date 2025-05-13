import base64
import io
import json
import logging
import re
from typing import Any

import markdown as mkd
from PIL import Image, UnidentifiedImageError
from django.template import Context, Library, Node
from django.template.base import NodeList, Parser

from ...core.flags import parse_bool
from ...core.utils import dict_get_nested, dict_setdefault, oneline
from ...i18n.get_text import gettext as _
from ...registration.models import Registration

logger = logging.getLogger(__name__)
register = Library()


class EscapeScriptNode(Node):
    def __init__(self, nodelist: NodeList) -> None:
        super().__init__()
        self.nodelist = nodelist

    def render(self, context: Context) -> str:
        out = self.nodelist.render(context)
        return out.replace("</script>", "<\\/script>")


@register.tag()
def escapescript(parser: Parser, token: str) -> Node:
    nodelist = parser.parse(("endescapescript",))
    parser.delete_first_token()
    return EscapeScriptNode(nodelist)


@register.filter
def islist(value: Any) -> bool:
    return isinstance(value, list | tuple)


@register.filter
def isstring(value: Any) -> bool:
    return isinstance(value, str)


@register.filter
def isdict(value: Any) -> bool:
    return isinstance(value, dict)


@register.inclusion_tag("dump/dump.html")
def dump(value: Any) -> dict[str, Any]:
    return {"value": value}


@register.inclusion_tag("dump/list.html")
def dump_list(value: list) -> dict[str, Any]:
    return {"value": value}


@register.inclusion_tag("dump/dict.html")
def dump_dict(value: dict) -> dict[str, Any]:
    return {"value": value}


@register.filter(name="smart")
def smart_attr(field: Any, attr: str) -> str:
    translate = False
    if "," in attr:
        attr, translate = attr.split(",")
    value = field.field.flex_field.advanced.get("smart", {}).get(attr, "")
    if parse_bool(translate):
        value = _(str(value))
    return str(value)


@register.filter()
def jsonfy(d: Any) -> str:
    return json.dumps(d, indent=3)


@register.filter(name="lookup")
def lookup(value: dict[str, Any], arg: str) -> Any:
    return value.get(arg)


@register.filter()
def is_image(element: str) -> bool:
    if not isinstance(element, str) or len(element) < 200:
        return False
    try:
        imgdata = base64.b64decode(str(element))
        im = Image.open(io.BytesIO(imgdata))
        im.verify()
        return True
    except UnidentifiedImageError:
        return False


@register.filter()
def is_base64(element: str) -> bool:
    expression = "^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$"
    try:
        if isinstance(element, str) and element.strip().endswith("=="):
            return re.match(expression, element)
    except Exception as e:
        logger.exception(e)
    return False


@register.inclusion_tag("buttons/link.html")
def link(registration: Registration) -> str:
    config = registration.advanced.copy()
    config = dict_setdefault(config, Registration.ADVANCED_DEFAULT_ATTRS)
    widget = dict_get_nested(config, "smart.buttons.link.widget")
    attrs = dict_get_nested(widget, "attrs")

    if "class" not in attrs:
        widget["attrs"]["class"] = "button bg-blue border-0 py-4 px-8 rounded text-center text-2xl"

    widget["attrs"]["href"] = registration.get_welcome_url() + f"?reg={registration.slug}"
    return {
        "reg": registration,
        "widget": widget,
    }


@register.filter()
def markdown(value: str) -> str:
    if value:
        return mkd.markdown(value, extensions=["markdown.extensions.fenced_code"])
    return ""


@register.filter()
def md(value: str) -> str:
    if value:
        p = mkd.markdown(value, extensions=["markdown.extensions.fenced_code"])
        return p.replace("<p>", "").replace("</p>", "")
    return ""


@register.filter(name="oneline")
def _oneline(value: str) -> str:
    return oneline(value)
