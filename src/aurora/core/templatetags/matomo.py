from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag()
def matomo_site():
    return settings.MATOMO_SITE


@register.simple_tag()
def matomo_id():
    return settings.MATOMO_ID
