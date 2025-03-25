import pytest
from django import forms
from testutils.selenium import AuroraTestBrowser
from testutils.factories import ProjectFactory

from aurora.core.models import FlexForm
from aurora.registration.models import Record
from strategy_field.utils import fqn

from aurora.management.commands.ukr import upgrade

pytestmark = pytest.mark.selenium


@pytest.fixture
def project():
    return ProjectFactory()


@pytest.fixture
def ukraine_form(project):
    from aurora.core.cache import cache

    cache.clear()

    upgrade()
    base_form = FlexForm.objects.get(name="Basic")
    return base_form


@pytest.fixture
def ukraine_registration(ukraine_form, project):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="Ucraina",
        flex_form=ukraine_form,
        intro="Some intro text",
        project=project,
    )


def test_register_success(browser: AuroraTestBrowser, ukraine_registration):
    url = ukraine_registration.get_absolute_url()
    browser.open(url)

    browser.check("input[name=enum_org][value=unicef]")
    browser.check("input[name=enum_org][value=gov_partner]")

    browser.choose("select[name=residence_status]", "idp")

    browser.select2("select[name=household-0-admin_1]", "Region1")
    browser.wait_for_element("select[name=household-0-admin_2]")
    browser.select2("select[name=household-0-admin_2]", "District2")
    browser.wait_for_element("select[name=household-0-admin_3]")
    browser.select2("select[name=household-0-admin_3]", "Community1")

    browser.type("input[name=individual-0-first_name]", "Іван")
    browser.type("input[name=individual-0-last_name]", "Петренко")

    browser.click("a:contains('Add another Individual')")
    browser.type("input[name=individual-1-first_name]", "Олена")
    browser.type("input[name=individual-1-last_name]", "Петренко")

    browser.click("input[name=_save_form]")
    reg_id = browser.get_text("#registration-id")
    browser.click("a:contains('register another household')")
    assert Record.objects.filter(id=reg_id.split("/")[1]).exists()


def test_register_errors(browser: AuroraTestBrowser, ukraine_registration):
    url = ukraine_registration.get_absolute_url()
    browser.open(url)
    browser.click("input[name=_save_form]")
    browser.assert_text("This field is required.", "li:contains('With whom may we share')")
    browser.assert_text("This field is required.", "li:contains('Residence status')")
    browser.assert_text("This field is required.", "li:contains('Admin 1')")
    browser.assert_text("This field is required.", "li:contains('First Name'):eq(0)")
    browser.assert_text("This field is required.", "li:contains('Last Name'):eq(0)")
    browser.assert_text("This field is required.", "li:contains('First Name'):eq(1)")
    browser.assert_text("This field is required.", "li:contains('Last Name'):eq(1)") 
