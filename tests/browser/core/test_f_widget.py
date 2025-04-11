from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from testutils.factories import FlexFormFieldFactory, FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
from aurora.core.models import FlexFormField

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
def registration():
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    FlexFormFieldFactory(
        flex_form=frm,
        name="field1",
        required=True,
        advanced={
            **FlexFormField.FLEX_FIELD_DEFAULT_ATTRS,
            "widget": {
                "placeholder": "placeholder_text",
                "extra_classes": "extra-test-class",
            },
            "smart": {
                "hint": "hint text",
                "description": "description text",
            },
        },
        field_type=fields.CharField,
    )
    FlexFormFieldFactory(
        flex_form=frm,
        name="field2",
        required=True,
        advanced={
            **FlexFormField.FLEX_FIELD_DEFAULT_ATTRS,
            "smart": {
                "question": "question text",
            },
        },
        field_type=fields.CharField,
    )
    return RegistrationFactory(name="registration #3", flex_form=frm, encrypt_data=False)


def test_widget_attrs(mock_state, browser: AuroraTestBrowser, registration: "Registration"):
    url = registration.get_absolute_url()
    browser.open(url)
    browser.wait_for_element_not_visible("#loading")
    assert browser.get_element("input.extra-test-class")
    assert browser.get_element("div.itrans.text-sm.description").text == "description text"
    assert browser.get_element("div.itrans.text-xs.italic.hint").text == "hint text"
    assert browser.get_element("input[type=text][name=field1]").get_attribute("placeholder") == "placeholder_text"


def test_widget_attrs_question(mock_state, browser: AuroraTestBrowser, registration: "Registration"):
    url = registration.get_absolute_url()
    browser.open(url)
    browser.wait_for_element_not_visible("#loading")
    browser.assert_element_not_visible("div.field-container.field-container-field2")
    browser.click("#question_id_field2")
    browser.assert_element_visible("div.field-container.field-container-field2")
