from unittest.mock import Mock

import pytest
from testutils.factories import FlexFormFieldFactory, FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
from aurora.core.models import FlexFormField
from aurora.registration.models import Record

pytestmark = pytest.mark.selenium


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())
    yield
    state.request = None


@pytest.fixture
def registration(birth_after_1900):
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    FlexFormFieldFactory(flex_form=frm, name="verified_disability", required=False)
    FlexFormFieldFactory(
        flex_form=frm,
        name="yes_no",
        field_type=fields.YesNoRadio,
        advanced={
            **FlexFormField.FLEX_FIELD_DEFAULT_ATTRS,
            "smart": {
                "visible": True,
            },
            "events": {
                "onchange": """
var f = new aurora.Field(this);
f.sibling('verified_disability').setRequired(f.getValue() === 'y' );
"""
            },
        },
        required=False,
    )

    return RegistrationFactory(
        name="registration #3",
        flex_form=frm,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


def test_register2(mock_state, browser: AuroraTestBrowser, registration):
    url = registration.get_absolute_url()
    browser.open(url)
    browser.wait_for_element_not_visible("#loading")
    browser.click("input[name=yes_no][value='y']")
    assert browser.is_required("input[name='verified_disability']")

    browser.click("input[name=yes_no][value='n']")
    assert not browser.is_required("input[name='verified_disability']")
    browser.click("input[name=_save_form]")
    reg_id = browser.get_text("#registration-id")
    assert Record.objects.filter(id=reg_id.split("/")[1])
