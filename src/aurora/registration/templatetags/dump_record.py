import base64
import io
import logging
import re
from typing import Any, reveal_type

from PIL import Image, UnidentifiedImageError
from django.template import Context, Library, Node
from django.template.base import NodeList, Parser, Token

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
def escapescript(parser: Parser, token: Token) -> EscapeScriptNode:
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
def dump(value: Any, key: Any | None = None, original: Any | None = None) -> dict[str, Any]:
    return {"value": value, "key": key, "original": original}


@register.inclusion_tag("dump/list.html")
def dump_list(value: Any, key: Any | None = None, original: Any | None = None) -> dict[str, Any]:
    return {"value": value, "key": key, "original": original}


@register.inclusion_tag("dump/dict.html")
def dump_dict(value: Any, key: Any | None = None, original: Any | None = None) -> dict[str, Any]:
    return {"value": value, "key": key, "original": original}


@register.filter(name="smart")
def smart_attr(field, attr: str) -> str:
    print(111.1, 111111, reveal_type(field))
    return field.field.flex_field.advanced.get("smart", {}).get(attr, "")


@register.filter(name="lookup")
def lookup(value: dict[Any, Any], arg: Any) -> Any:
    return value.get(arg, None)


@register.filter()
def is_image(element: Any) -> bool:
    if not isinstance(element, str) or len(element) < 200:
        return False
    try:
        imgdata = base64.b64decode(str(element))
        im = Image.open(io.BytesIO(imgdata))
        im.verify()
        return True
    except (UnidentifiedImageError, ValueError):
        return None


@register.filter()
def is_base64(element: Any) -> bool:
    expression = "^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$"
    try:
        if isinstance(element, str) and element.strip().endswith("=="):
            return re.match(expression, element)
    except Exception as e:
        logger.exception(e)
    return False


@register.filter
def concat(a: Any, b: Any) -> str:
    """Concatenate arg1 & arg2."""
    return "".join(map(str, (a, b)))
