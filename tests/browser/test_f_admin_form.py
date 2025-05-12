import pytest

from testutils.factories import FlexFormFieldFactory, FormFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core.fields import (
    MultiCheckboxField,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aurora.core.models import FlexForm


pytestmark = pytest.mark.selenium


@pytest.fixture
def form_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Form", target=Validator.FORM, active=True, code=code)


@pytest.fixture
def flex_form(db, form_validator) -> "FlexForm":
    form = FormFactory(name="Form1", validator=form_validator)
    FlexFormFieldFactory(
        flex_form=form,
        label="FlexField1",
        name="flexfield-mc1",
        field_type=MultiCheckboxField,
        choices="a,b,c",
        advanced={"smart": {"visible": True}},
    )
    return form


def test_multicheckboxfield_field(browser: AuroraTestBrowser, flex_form):
    browser.open("/admin/")
    browser.login()
    browser.click_link("Flex Forms")
    browser.click_link(flex_form.name)
    browser.click('a:contains("editor")')
    browser.click("#radio_display")
    browser.switch_to_frame("#widget_display")
    browser.wait_for_ready_state_complete()
