import logging

from django.core.cache import caches
from django.utils import timezone
from django_redis import get_redis_connection

from ..state import state
from .models import Message

logger = logging.getLogger(__name__)

cache = caches["default"]


class Dictionary:
    def __init__(self, locale):
        self.locale = locale
        self.messages = {}
        self._loaded = False

    def reset(self):
        self.messages = {}

    def load_all(self):
        entries = Message.objects.filter(locale=self.locale, draft=False).values("msgid", "msgstr")
        self.messages = {k["msgid"]: k["msgstr"] for k in entries}
        self._loaded = True

    def __getitem__(self, msgid):
        translation = msgid or ""
        if not msgid.strip():
            return translation
        try:
            if state.collect_messages:
                session = state.request.headers["I18N_SESSION"]
                con = get_redis_connection("default")
                con.lpush(session, str(msgid).encode())
            if getattr(self, "hit_messages", False):
                raise KeyError("--")
            translation = self.messages[msgid]
        except KeyError:
            if state.collect_messages:
                msg = None
                try:
                    msg = Message.objects.get(locale=self.locale, msgid__iexact=str(msgid))
                    if not msg.draft:
                        translation = msg.msgstr
                except Message.MultipleObjectsReturned as e:
                    logger.exception(e)
                    msg = Message.objects.filter(locale=self.locale, msgid__iexact=str(msgid)).first()
                    if not msg.draft:
                        translation = msg.msgstr or ""
                except Message.DoesNotExist:
                    msg, __ = Message.objects.get_or_create(msgid=msgid, locale=self.locale, defaults={"msgstr": msgid})
                    translation = msg.msgstr
                finally:
                    if getattr(state, "hit_messages", False) and msg:
                        Message.objects.filter(id=msg.pk).update(last_hit=timezone.now(), used=True)

        return translation or ""


class Cache:
    def __init__(self):
        self.locales = {}

    def reset(self):
        for __, locale in self.locales.items():
            locale.reset()

    def activate(self, locale):
        e = self[locale]
        e.load_all()
        return e

    def __getitem__(self, locale):
        try:
            entry = self.locales[locale]
        except KeyError:
            entry = Dictionary(locale)
            self.locales[locale] = entry
        return entry


translator = Cache()
del Cache
