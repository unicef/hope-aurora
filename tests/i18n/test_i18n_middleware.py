from unittest.mock import Mock, patch

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory

from aurora.i18n.engine import translator
from aurora.web.middlewares.i18n import I18NMiddleware


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser(), headers={"I18N_SESSION": "abc"})
    yield state
    state.request = None
    state.data = {"collect_messages": False, "hit_messages": False}


def test_middleware_lang(db, mock_state):
    def get_response(req: HttpRequest):
        return HttpResponse("Ok")

    mdw = I18NMiddleware(get_response)

    req = RequestFactory(headers={"ACCEPT_LANGUAGE": "it"}).get("/")
    assert mdw(req).status_code == 200
    assert translator.active_locale == "it-it"

    req = RequestFactory(headers={"ACCEPT_LANGUAGE": "it"}).get("/en-us/")
    assert mdw(req).status_code == 200
    assert translator.active_locale == "en-us"


def test_middleware_collect(db, mock_state):
    def get_response(req: HttpRequest):
        return HttpResponse("Ok")

    mdw = I18NMiddleware(get_response)
    req = RequestFactory(headers={"I18N_SESSION": "abc"}).get("/")
    with patch.object(translator["en-us"], "reset") as m:
        assert mdw(req).status_code == 200
        m.assert_called()
