import datetime
import decimal
import json
import re
import unicodedata

from constance import config
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.template import loader
from django.utils.functional import keep_lazy_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.utils.timezone import is_aware


def is_root(request, *args, **kwargs):
    return request.user.is_superuser and request.headers.get("x-root-token") == settings.ROOT_TOKEN


@keep_lazy_text
def namify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize("NFKC", value)
    else:
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return slugify(re.sub(r"[-\s]+", "_", value).strip("-_"))


class JSONEncoder(DjangoJSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time and decimal types.
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            r = o.isoformat()
            if o.microsecond:
                r = r[:23] + r[26:]
            if r.endswith("+00:00"):
                r = r[:-6] + "Z"
            return r
        elif isinstance(o, datetime.date):
            return o.isoformat()
        elif isinstance(o, datetime.time):
            if is_aware(o):
                raise ValueError("JSON can't represent timezone-aware times.")
            r = o.isoformat()
            if o.microsecond:
                r = r[:12]
            return r
        elif isinstance(o, set):
            return list(o)
        elif isinstance(o, decimal.Decimal):
            return str(o)
        elif isinstance(o, bytes):
            return str(o, encoding="utf-8")
        else:
            return super().default(o)


def safe_json(data):
    return json.dumps(data, cls=JSONEncoder)


def jsonfy(data):
    return json.loads(safe_json(data))


def underscore_to_camelcase(value):
    return value[0].upper() + "".join(
        list(
            map(
                lambda index_word: index_word[1].lower()
                if index_word[0] == 0
                else index_word[1][0].upper() + (index_word[1][1:] if len(index_word[1]) > 0 else ""),
                list(enumerate(re.split(re.compile(r"[_ ]+"), value[1:]))),
            )
        )
    )


def render(request, template_name, context=None, content_type=None, status=None, using=None, cookies=None):
    """
    Return a HttpResponse whose content is filled with the result of calling
    django.template.loader.render_to_string() with the passed arguments.
    """
    content = loader.render_to_string(template_name, context, request, using=using)
    response = HttpResponse(content, content_type, status)
    if cookies:
        for k, v in cookies.items():
            response.set_cookie(k, v)

    return response


def clean(v):
    return v.replace(r"\n", "").strip()


def get_bookmarks(request):
    quick_links = []
    for entry in config.SMART_ADMIN_BOOKMARKS.split("\n"):
        if entry := clean(entry):
            try:
                if entry == "--":
                    quick_links.append(mark_safe("<li><hr/></li>"))
                elif parts := entry.split(","):
                    args = None
                    if len(parts) == 1:
                        args = parts[0], "viewlink", parts[0], parts[0]
                    elif len(parts) == 2:
                        args = parts[0], "viewlink", parts[1], parts[0]
                    elif len(parts) == 3:
                        args = parts[0], "viewlink", parts[1], parts[0]
                    elif len(parts) == 4:
                        args = parts.reverse()
                    if args:
                        quick_links.append(format_html('<li><a target="{}" class="{}" href="{}">{}</a></li>', *args))
            except ValueError:
                pass
    return quick_links
