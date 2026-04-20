import django_stubs_ext as django_stubs

from .celery import app as celery_app  # noqa
from .version import __version__  # noqa

django_stubs.monkeypatch()


VERSION = "1.7.0"  #  __version__
