from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag()
def matomo_site() -> str:
    return settings.MATOMO_SITE


@register.simple_tag()
def matomo_id() -> str:
    return getattr(settings, "MATOMO_ID", "")
