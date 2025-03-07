import hashlib

from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext_lazy as _
from natural_keys import NaturalKeyModel

from .fields import LanguageField


class I18NModel:
    I18N_FIELDS = []
    I18N_ADVANCED = []


class Message(NaturalKeyModel):
    timestamp = models.DateTimeField(auto_now_add=True)
    locale = LanguageField(db_index=True)
    msgid = models.TextField(db_index=True)
    msgstr = models.TextField(blank=True, null=True)
    md5: str = models.CharField(verbose_name=_("MD5"), max_length=512, null=False, blank=False, unique=True)
    msgcode: str = models.CharField(verbose_name=_("Code"), max_length=512, null=False, blank=False)
    auto = models.BooleanField(default=False)
    draft = models.BooleanField(default=True)
    used = models.BooleanField(default=True)
    last_hit = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("msgid", "locale")

    def __str__(self):
        return f"{truncatechars(self.msgid, 60)}"

    @staticmethod
    def get_md5(msgid, locale=""):
        return hashlib.md5((msgid + "|" + locale).encode()).hexdigest()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.md5 = self.get_md5(self.msgid, self.locale)
        self.msgcode = self.get_md5(self.msgid)
        obj: Message = super().save()
        return obj
