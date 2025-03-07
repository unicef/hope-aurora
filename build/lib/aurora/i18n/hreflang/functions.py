from functools import lru_cache

from django.conf import settings
from django.urls.base import resolve
from django.urls.base import reverse as lang_implied_reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import activate, deactivate, get_language, override


def reverse(view_name, lang=None, use_lang_prefix=True, *args, **kwargs):
    """
    Similar to django.core.urlresolvers.reverse except for the parameters.

    :param lang: Language code in which the url is to be translated (ignored if use_lang_prefix is False).
    :param use_lang_prefix: If changed to False, get an url without language prefix.

    If lang is not provided, the normal reverse behaviour is obtained.
    """
    # todo: use_lang_prefix implementation is a bit of a hack now
    #  until a better way is found:
    #  http://stackoverflow.com/questions/27680748/when-using-i18n-patterns-how-to-reverse-url-without-language-code
    if lang is None:
        with override(None):
            return lang_implied_reverse(view_name, args=args, kwargs=kwargs)
    cur_language = get_language()
    if use_lang_prefix:
        activate(lang)
    else:
        deactivate()
    url = lang_implied_reverse(view_name, args=args, kwargs=kwargs)
    if not use_lang_prefix:
        if not url.startswith(f"/{settings.LANGUAGE_CODE}"):
            raise NoReverseMatch(f'could not find reverse match for "{view_name}" with language "{lang}"')
        url = url[1 + len(settings.LANGUAGE_CODE):]  # fmt: skip
    activate(cur_language)
    return url


def get_hreflang_info(path, default=True):
    """
    Return a list of (code, url) tuples for all language versions.

    :param path: Current path (request.path).
    :param default: Include the default landing page (x-default without language code).
    """
    reverse_match = resolve(path)
    info = []
    if default:
        info.append(
            (
                "x-default",
                reverse(
                    reverse_match.view_name,
                    use_lang_prefix=False,
                    kwargs=reverse_match.kwargs,
                ),
            )
        )
    return [
        (
            lang,
            reverse(
                reverse_match.view_name,
                lang=lang,
                use_lang_prefix=True,
                kwargs=reverse_match.kwargs,
            ),
        )
        for lang in language_codes()
    ]


@lru_cache
def languages():
    """Get language and regionale codes and names of all languages that are supported as a dictionary."""
    return dict(settings.LANGUAGES)


@lru_cache
def language_codes():
    """Get language with regionale codes of all languages that are supported."""
    return languages().keys()
