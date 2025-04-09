import pytest
from testutils.factories import MessageFactory

from aurora.i18n.models import Message


def test_message(db):
    msg: Message = Message(msgid="name")
    msg.save()
    assert str(msg) == "name"


def test_update_or_create_translation(db):
    msg: Message = MessageFactory(msgid="name")
    m2: Message = msg.update_or_create_translation("nome", "it")[0]

    assert m2.msgcode == msg.msgcode
    assert m2.md5 != msg.md5

    assert str(msg) == "name"
    assert str(m2) == "name"
    assert m2.msgstr == "nome"


def test_update_or_create_translation_forbidden_for_not_saved_objects(db):
    msg: Message = Message(msgid="name")
    with pytest.raises(Exception, match="Cannot create translation for not saved messages"):
        msg.update_or_create_translation("nome", "it")


def test_get_siblings(db):
    msg: Message = MessageFactory(msgid="name")
    m2 = msg.update_or_create_translation("nome", "it")[0]
    assert m2.msgcode == msg.msgcode

    assert m2.msgid == msg.msgid
    assert len(msg.get_siblings()) == 2
