from logging import warning

from django.conf import settings

from .functions import get_hreflang_info, language_codes, languages, reverse  # noqa
from .header import AddHreflangToResponse, hreflang_headers  # noqa

if not getattr(settings, "DISABLE_LOCALE_MIDDLEWARE_CHECK", False) and not any(
    "LocaleMiddleware" in mw for mw in settings.MIDDLEWARE
):
    warning("LocaleMiddleware is not turned on, hreflang (and i18n generally) may experience problems.")

# default __all__ is fine
