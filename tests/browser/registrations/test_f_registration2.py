from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest
from selenium.webdriver import Keys
from testutils.factories import FlexFormFieldFactory, FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
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
        name="date_of_birth",
        field_type=fields.DateField,
        required=True,
        validator=birth_after_1900,
        advanced={
            "smart": {
                "visible": True,
            },
            "events": {
                "onchange": """
                                     var f = new aurora.Field(this);
                                     var bd = f.sibling('date_of_birth');
                                     console.log(11111, bd.getValue());
                                     if (smart.is_adult(bd.getValue())){
                                        f.sibling('verified_disability').setRequired(true);
                                     }else{
                                        f.sibling('verified_disability').setRequired(false).setValue('');
                                     }
                                    """
            },
        },
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
    now = datetime.now()  # current date and time
    young = (now - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
    adult = (now - timedelta(days=365 * 30)).strftime("%Y-%m-%d")

    assert not browser.is_required("input[name='verified_disability']")

    browser.type("input[name=date_of_birth]", young)
    browser.send_keys("input[name=date_of_birth]", Keys.TAB)
    assert not browser.is_required("input[name='verified_disability']")

    browser.type("input[name=date_of_birth]", adult)
    browser.send_keys("input[name=date_of_birth]", Keys.TAB)
    assert browser.is_required("input[name='verified_disability']")

    browser.click("input[name=_save_form]")
    browser.type("input[name=verified_disability]", "verified_disability")
    browser.click("input[name=_save_form]")

    reg_id = browser.get_text("#registration-id")
    assert Record.objects.filter(id=reg_id.split("/")[1])
