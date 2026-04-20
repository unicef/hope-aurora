import hashlib
from typing import TYPE_CHECKING

from django.db import models
from django.template.defaultfilters import truncatechars
from django.utils.translation import gettext_lazy as _
from natural_keys import NaturalKeyModel

from .fields import LanguageField

if TYPE_CHECKING:
    from django.db.models import QuerySet


class I18NModel:
    I18N_FIELDS: list[str] = []
    I18N_ADVANCED: list[str] = []


class Message(NaturalKeyModel):
    timestamp = models.DateTimeField(auto_now_add=True)
    locale = LanguageField(db_index=True, help_text="The locale of the message.")
    msgid = models.TextField(db_index=True, help_text="Original message value")
    msgstr = models.TextField(blank=True, null=True, help_text="Localized Message content.")

    md5 = models.CharField(
        verbose_name=_("MD5"),
        max_length=512,
        null=False,
        blank=False,
        unique=True,
        help_text="Localised code of the message",
    )
    msgcode = models.CharField(
        verbose_name=_("Code"),
        max_length=512,
        null=False,
        blank=False,
        help_text="Code of the message. It is shared between translations of same message.",
    )

    auto = models.BooleanField(default=False, help_text="Is this message auto-generated?")
    draft = models.BooleanField(default=True, help_text="If draft the message is not used in translation")
    used = models.BooleanField(default=True, help_text="Is this message used somewhere in Aurora?")
    last_hit = models.DateTimeField(
        blank=True, null=True, help_text="Last time this translation hase been used message"
    )

    class Meta:
        unique_together = ("msgid", "locale")

    def __str__(self) -> str:
        return f"{truncatechars(self.msgid, 60)}"

    @staticmethod
    def get_md5(msgid: str, locale: str = "") -> str:
        return hashlib.md5((msgid + "|" + locale).encode()).hexdigest()  # noqa: S324

    def save(
        self, force_insert: bool = False, force_update: bool = False, using: str = None, update_fields: list[str] = None
    ) -> None:
        self.md5 = self.get_md5(self.msgid, self.locale)
        self.msgcode = self.get_md5(self.msgid)
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)

    def get_siblings(self) -> "QuerySet[Message]":
        return Message.objects.filter(msgcode=self.msgcode)

    def update_or_create_translation(
        self, value: str, locale: str, draft: bool = True
    ) -> "tuple[Message, bool] | None":
        if not self.pk:
            raise Exception("Cannot create translation for not saved messages")
        return Message.objects.update_or_create(
            msgid=self.msgid,
            locale=locale,
            defaults={
                "msgcode": self.get_md5(self.msgid),
                "md5": self.get_md5(self.msgid, self.locale),
                "msgstr": value,
                "draft": draft,
            },
        )
