"""
Create hreflang tags as specified by Google.

https://support.google.com/webmasters/answer/189077?hl=en
"""

from django import template
from django.urls import NoReverseMatch
from django.urls.base import resolve
from django.utils.translation import get_language

from aurora.core.utils import cache_aware_url
from aurora.i18n.hreflang import get_hreflang_info, languages, reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context, lang, view_name=None, *args, **kwargs):
    """
    Translate an url to a specific language.

    @param lang: Which language should the url be translated to.
    @param view_name: Which view to get url from, current if not set.
    """
    if "request" not in context:
        raise Exception("translate_url needs request context")
    try:
        kwargs["lang"] = lang
        if view_name is None:
            reverse_match = resolve(context["request"].path)
            view_name = reverse_match.view_name
            args = reverse_match.args
            kwargs = reverse_match.kwargs
        return cache_aware_url(context["request"], reverse(view_name, *args, **kwargs))
    except NoReverseMatch:
        return ""


@register.simple_tag(takes_context=True)
def hreflang_tags(context, indent=0):
    """Create all hreflang <link> tags (which includes the current document as per the standard)."""
    if "request" not in context:
        raise Exception("hreflang_tags needs request context")
    hreflang_info = get_hreflang_info(context["request"].path)
    hreflang_html = []
    for lang, url in hreflang_info:
        hreflang_html.append(f'<link rel="alternate" hreflang="{lang}" href="{url}" />\n')
    return ("\t" * indent).join(hreflang_html)


def _make_list_html(path, incl_current):
    hreflang_info = get_hreflang_info(path, default=False)
    hreflang_html = ""
    for lang, url in hreflang_info:
        if lang == get_language() and incl_current:
            hreflang_html += f'<li class="hreflang_current_language"><strong>{languages()[lang]}</strong></li>\n'
        else:
            hreflang_html += f'<li><a href="{url}" >{languages()[lang]}</a></li>\n'
    return hreflang_html


@register.simple_tag(takes_context=True)
def lang_list(context):
    """
    HTML list items with links to each language version of this document.

    The current document is included without link and with a special .hreflang_current_language class.
    """
    if "request" not in context:
        raise Exception("lang_list needs request context")
    return _make_list_html(context["request"].path, incl_current=True)


@register.simple_tag(takes_context=True)
def other_lang_list(context):
    """Like lang_list, but the current language is excluded."""
    if "request" not in context:
        raise Exception("other_lang_list needs request context")
    return _make_list_html(context["request"].path, incl_current=False)
