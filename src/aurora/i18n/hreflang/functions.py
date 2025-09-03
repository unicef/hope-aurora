from django.conf import settings
from django.urls.base import reverse as lang_implied_reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.translation import deactivate, get_language, override

from aurora.i18n.engine import translator


def reverse(view_name: str, lang: str = None, use_lang_prefix: bool = True, *args, **kwargs) -> str:
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
        translator.activate(lang)
    else:
        deactivate()
    url = lang_implied_reverse(view_name, args=args, kwargs=kwargs)
    if not use_lang_prefix:
        if not url.startswith(f"/{settings.LANGUAGE_CODE}"):
            raise NoReverseMatch(f'could not find reverse match for "{view_name}" with language "{lang}"')
        url = url[1 + len(settings.LANGUAGE_CODE):]  # fmt: skip
    translator.activate(cur_language)
    return url
