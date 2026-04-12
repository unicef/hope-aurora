import django_stubs_ext as django_stubs

from .config.celery import app as celery_app  # noqa
from .version import __version__

django_stubs.monkeypatch()
VERSION = __version__


__all__ = ["VERSION", "__version__", "celery_app"]
