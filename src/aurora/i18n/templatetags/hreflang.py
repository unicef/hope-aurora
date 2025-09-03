"""
Create hreflang tags as specified by Google.

https://support.google.com/webmasters/answer/189077?hl=en
"""

from typing import Any

from django import template
from django.urls import NoReverseMatch
from django.urls.base import resolve

from aurora.core.utils import cache_aware_url
from aurora.i18n.hreflang import reverse

register = template.Library()


@register.simple_tag(takes_context=True)
def translate_url(context: dict[str, Any], lang: str, view_name: str | None = None, *args, **kwargs) -> str:
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
