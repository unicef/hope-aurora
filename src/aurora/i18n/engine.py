import logging

from django.core.cache import caches
from django.utils import timezone
from django.utils.translation import activate
from django_redis import get_redis_connection

from ..state import state
from .models import Message

logger = logging.getLogger(__name__)

cache = caches["default"]


class Dictionary:
    def __init__(self, locale: str) -> None:
        self.locale = locale
        self.messages: dict[str, str] = {}
        self._loaded = False

    def reset(self) -> None:
        self.messages = {}

    def load_all(self) -> None:
        entries = Message.objects.filter(locale=self.locale, draft=False).values("msgid", "msgstr")
        self.messages = {k["msgid"]: k["msgstr"] for k in entries}
        self._loaded = True

    def ngettext(self, singular: str, plural: str, count: int) -> str:
        if count > 1:
            return self[plural]
        return self[singular]

    def __getitem__(self, msgid: str) -> str:
        translation = msgid or ""
        if not msgid.strip():
            return translation
        try:
            if state.collect_messages:
                session = state.request.headers["I18N_SESSION"]
                con = get_redis_connection("default")
                con.lpush(session, str(msgid).encode())
            translation = self.messages[msgid]
        except KeyError:
            if state.collect_messages:
                msg = None
                try:
                    msg = Message.objects.get(locale=self.locale, msgid__iexact=str(msgid))
                    if not msg.draft:
                        translation = msg.msgstr
                except Message.DoesNotExist:
                    msg, __ = Message.objects.get_or_create(msgid=msgid, locale=self.locale, defaults={"msgstr": msgid})
                    translation = msg.msgstr
                finally:
                    if getattr(state, "hit_messages", False) and msg:
                        Message.objects.filter(id=msg.pk).update(last_hit=timezone.now(), used=True)

        return translation or ""


class Cache:
    def __init__(self) -> None:
        self.locales: dict[str, Dictionary] = {}
        self.active_locale: str | None = None

    def reset(self) -> None:
        for locale in self.locales.values():
            locale.reset()

    def activate(self, locale: str) -> Dictionary:
        self.active_locale = locale
        activate(locale)
        e = self[locale]
        e.load_all()
        return e

    def __getitem__(self, locale: str) -> Dictionary:
        try:
            entry = self.locales[locale]
        except KeyError:
            entry = Dictionary(locale)
            self.locales[locale] = entry
        return entry


translator = Cache()
# del Cache
