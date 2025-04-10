from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from django.urls import reverse
from testutils.factories import MessageFactory
from testutils.selenium import AuroraTestBrowser

if TYPE_CHECKING:
    from aurora.registration.models import Registration

pytestmark = pytest.mark.selenium


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())
    yield
    state.request = None


@pytest.fixture
def record() -> "Registration":
    m1 = MessageFactory(msgstr="name", locale="en-us")
    m1.update_or_create_translation("nome", "it-it", draft=False)
    MessageFactory(msgstr="Date Of Birth", locale="en-us")
    return m1


def test_check_orphans(mock_state, browser: AuroraTestBrowser, record):
    url_list = reverse("admin:i18n_message_changelist")

    browser.login()
    browser.click(f"tr th a[href='{url_list}']")
    browser.click("#btn-check_orphans")
    browser.click("input[type=submit][value=Check]")


def test_create_translations(mock_state, browser: AuroraTestBrowser, record):
    url_list = reverse("admin:i18n_message_changelist")

    browser.login()
    browser.click(f"tr th a[href='{url_list}']")
    browser.click("#btn-create_translations")
    browser.click("input[type=submit][value=Create]")
