from typing import TYPE_CHECKING, Never, TypeVar

from django.contrib.sites.models import Site
from django.core import signals
from django.template.defaultfilters import slugify

from ..conf import settings

if TYPE_CHECKING:
    from ..models import Template as DBTemplate

    _T = TypeVar("_T")


def get_cache_backend() -> "_T":
    """Compatibilty wrapper for getting Django's cache backend instance."""
    from django.core.cache import caches

    cache = caches[settings.DBTEMPLATES_CACHE_BACKEND]
    # Some caches -- python-memcached in particular -- need to do a cleanup at
    # the end of a request cycle. If not implemented in a particular backend
    # cache.close is a no-op
    signals.request_finished.connect(cache.close)
    return cache


cache = get_cache_backend()


def get_cache_key(name: str) -> str:
    current_site = Site.objects.get_current()
    return "dbtemplates::%s::%s" % (slugify(name), current_site.pk)


def get_cache_notfound_key(name: str) -> str:
    return get_cache_key(name) + "::notfound"


def remove_notfound_key(instance: "DBTemplate") -> Never:
    # Remove notfound key as soon as we save the template.
    cache.delete(get_cache_notfound_key(instance.name))


def set_and_return(cache_key: str, content: str, display_name: str) -> tuple[str, str]:
    # Save in cache backend explicitly if manually deleted or invalidated
    if cache:
        cache.set(cache_key, content)
    return (content, display_name)


def add_template_to_cache(instance: "DBTemplate", **kwargs) -> Never:
    """
    Cache templates.

    Called via Django's signals to .
    if the template in the database was added or changed.
    """
    remove_cached_template(instance)
    remove_notfound_key(instance)
    if instance.active:
        cache.set(get_cache_key(instance.name), instance.content)


def remove_cached_template(instance: "DBTemplate", **kwargs) -> Never:
    """
    Remove cached templates.

    Called via Django's signals.
    If the template in the database was changed or deleted.
    """
    cache.delete(get_cache_key(instance.name))
