import logging
from collections import OrderedDict
from functools import wraps

from aurora.state import state

logger = logging.getLogger(__name__)


class Cache(OrderedDict):
    def __init__(self, *args, **kwds):
        self.size_limit = kwds.pop("size", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.size_limit is not None:
            while len(self) > self.size_limit:
                self.popitem(last=False)

    def clear(self):
        while len(self) > 0:
            self.popitem(last=False)


cache: Cache = Cache(size=100)


def cache_form(f):
    @wraps(f)
    def _inner(*args, **kwargs):
        key = f"{args[0].pk}-{args[0].version}-{state.request.LANGUAGE_CODE}"
        if key not in cache:
            logger.debug("cache missing")
            ret = f(*args, **kwargs)
            cache[key] = ret
        else:
            logger.debug("cache hit")

        return cache[key]

    return _inner


def cache_formset(f):
    @wraps(f)
    def _inner(*args, **kwargs):
        flex_form = args[0].registration.flex_form
        key = f"{flex_form.pk}-{flex_form.version}-formset-{state.request.LANGUAGE_CODE}"
        if key not in cache:
            logger.debug("cache missing")
            ret = f(*args, **kwargs)
            cache[key] = ret
        else:
            logger.debug("cache hit")

        return cache[key]

    return _inner
