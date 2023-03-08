import base64
import io
import json
import logging
import re

import markdown as md
from django.template import Library, Node
from django.utils.safestring import mark_safe
from PIL import Image, UnidentifiedImageError

from aurora.i18n.gettext import gettext as _

from ...core.flags import parse_bool
from ...core.utils import dict_get_nested, dict_setdefault, oneline
from ...registration.models import Registration

logger = logging.getLogger(__name__)
register = Library()


class EscapeScriptNode(Node):
    def __init__(self, nodelist):
        super(EscapeScriptNode, self).__init__()
        self.nodelist = nodelist

    def render(self, context):
        out = self.nodelist.render(context)
        escaped_out = out.replace("</script>", "<\\/script>")
        return escaped_out


@register.tag()
def escapescript(parser, token):
    nodelist = parser.parse(("endescapescript",))
    parser.delete_first_token()
    return EscapeScriptNode(nodelist)


@register.filter
def islist(value):
    return isinstance(value, (list, tuple))


@register.filter
def isstring(value):
    return isinstance(value, (str,))


@register.filter
def isdict(value):
    return isinstance(value, (dict,))


@register.inclusion_tag("dump/dump.html")
def dump(value):
    return {"value": value}


@register.inclusion_tag("dump/list.html")
def dump_list(value):
    return {"value": value}


@register.inclusion_tag("dump/dict.html")
def dump_dict(value):
    return {"value": value}


@register.filter(name="smart")
def smart_attr(field, attr):
    translate = False
    if "," in attr:
        attr, translate = attr.split(",")
    value = field.field.flex_field.advanced.get("smart", {}).get(attr, "")
    if parse_bool(translate):
        value = _(str(value))
    return str(value)


@register.filter()
def jsonfy(d):
    return json.dumps(d, indent=3)


@register.filter(name="lookup")
def lookup(value, arg):
    # value_dict = ast.literal_eval(value)
    return value.get(arg, None)


@register.filter()
def is_image(element):
    if not isinstance(element, str) or len(element) < 200:
        return False
    try:
        imgdata = base64.b64decode(str(element))
        im = Image.open(io.BytesIO(imgdata))
        im.verify()
        return True
    except UnidentifiedImageError:
        return None


@register.filter()
def is_base64(element):
    expression = "^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$"
    try:
        if isinstance(element, str) and element.strip().endswith("=="):
            return re.match(expression, element)
    except Exception as e:
        logger.exception(e)
    return False


@register.inclusion_tag("buttons/link.html")
def link(registration):
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
def markdown(value):
    if value:
        p = md.markdown(value, extensions=["markdown.extensions.fenced_code"])
        return mark_safe(p)
    return ""


@register.filter(name="md")
def _md(value):
    if value:
        p = md.markdown(value, extensions=["markdown.extensions.fenced_code"])
        return mark_safe(p.replace("<p>", "").replace("</p>", ""))
    return ""


@register.filter(name="oneline")
def _oneline(value):
    return oneline(value)
