from testutils.factories import Message, MessageFactory

from aurora.i18n.engine import translator
from aurora.i18n.get_text import gettext


def test_gettext_empty(db):
    assert gettext("") == ""
    assert gettext("\n") == "\n"


def test_gettext(db):
    m1: Message = MessageFactory(msgstr="name", locale="en-us")
    m2: Message = m1.update_or_create_translation("nome", "it", draft=False)[0]

    translator.activate("it")
    assert gettext("name") == m2.msgstr

    translator.activate("en-us")
    assert gettext("name") == m1.msgstr
