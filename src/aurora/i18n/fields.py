from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class LanguageField(models.CharField):
    """A language field for Django models."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("verbose_name", _("Language"))
        kwargs.setdefault("max_length", 10)
        kwargs.setdefault("default", settings.LANGUAGE_CODE)
        kwargs.setdefault("null", True)
        kwargs.setdefault("choices", settings.LANGUAGES)
        super().__init__(*args, **kwargs)
