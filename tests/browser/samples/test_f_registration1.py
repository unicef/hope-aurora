import pytest
from testutils.factories import FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
from aurora.registration.models import Record

pytestmark = pytest.mark.selenium


@pytest.fixture
def registration(birth_after_1900):
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    frm.fields.get_or_create(label="name", required=True, defaults={"field_type": fields.CharField})
    frm.fields.get_or_create(
        label="date_of_birth", required=True, defaults={"field_type": fields.DateField}, validator=birth_after_1900
    )

    return RegistrationFactory(
        name="registration #3",
        flex_form=frm,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


def test_register1(mock_state, browser: AuroraTestBrowser, registration):
    url = registration.get_absolute_url()
    browser.open(url)
    assert browser.is_required("input[name='name']")

    browser.click("input[name=date_of_birth")
    browser.wait_for_element_visible(".datepicker-grid")
    browser.click(".datepicker-grid>span.datepicker-cell.day.focused")
    browser.type("input[name=name]", "name")
    browser.click("input[name=_save_form]")
    reg_id = browser.get_text("#registration-id")
    assert Record.objects.filter(id=reg_id.split("/")[1])


def test_register2(mock_state, browser: AuroraTestBrowser, registration):
    url = registration.get_absolute_url()
    browser.open(url)
    browser.type("input[name=date_of_birth]", "1800-01-01")
    browser.type("input[name=name]", "name")
    browser.click("input[name=_save_form]")
    assert browser.get_field_error("date_of_birth") == "the date should be after 1900"
