from typing import TYPE_CHECKING, Generator
from unittest.mock import Mock

import pytest
from testutils.factories import MessageFactory

from aurora.i18n.engine import Cache

if TYPE_CHECKING:
    from aurora.i18n.models import Message


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser(), headers={"I18N_SESSION": "abc"})
    yield state
    state.request = None
    state.data = {"collect_messages": False, "hit_messages": False}


@pytest.fixture
def engine(db) -> Generator[Cache, None, None]:
    m1: Message = MessageFactory(msgstr="First Name")
    m1.update_or_create_translation("Nome", "it", False)
    m1.update_or_create_translation("Nom", "fr", True)

    m1: Message = MessageFactory(msgstr="Last Name")
    m1.update_or_create_translation("Cognome", "it", False)
    c = Cache()
    c.reset()
    yield c
    c.reset()


@pytest.mark.parametrize("locale", ["it", "en-us"])
def test_engine_activate(engine, locale):
    assert engine.activate(locale).locale == locale


@pytest.mark.parametrize(
    "locale,pk,value",
    [
        ("it", "First Name", "Nome"),
        ("it", "Last Name", "Cognome"),
        ("en-us", "First Name", "First Name"),
        ("en-us", "Last Name", "Last Name"),
    ],
)
def test_engine_translation(engine: Cache, locale, pk, value):
    engine.activate(locale)
    assert engine[locale][pk] == value


def test_engine_collect(engine: Cache, mock_state):
    mock_state.collect_messages = True
    engine.activate("en")
    assert engine["en-us"]["First Name"] == "First Name"

    engine.activate("fr")
    assert engine["fr"]["First Name"] == "First Name"

    engine.activate("de")
    assert engine["de"]["First Name"] == "First Name"


def test_engine_hit_messages(engine: Cache, mock_state):
    mock_state.collect_messages = True
    mock_state.hit_messages = True
    engine.activate("en")
    assert engine["en-us"]["First Name"] == "First Name"

    engine.activate("fr")
    assert engine["fr"]["First Name"] == "First Name"

    engine.activate("de")
    assert engine["de"]["First Name"] == "First Name"
