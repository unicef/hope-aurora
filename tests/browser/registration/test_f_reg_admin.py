from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.urls import reverse
from testutils.factories import FlexFormFieldFactory, FormFactory, OptionSetFactory, RecordFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
from aurora.registration.models import Record, Registration

if TYPE_CHECKING:
    from aurora.core.models import OptionSet

pytestmark = pytest.mark.selenium


@pytest.fixture
def registration(birth_after_1900):
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    opt1: OptionSet = OptionSetFactory(
        name="optionset1",
        separator=";",
        pk_col=0,
        parent_col=-1,
        locale="en-us",
        languages="-,-,en-us",
        data="""0;0;----\r
UA01;UA;Admin1\r
UA02;UA;Admin2\r
UA03;UA;Admin3\r
""",
    )

    opt2: OptionSet = OptionSetFactory(
        name="optionset2",
        separator=";",
        pk_col=0,
        parent_col=1,
        locale="en-us",
        languages="-,-,en-us",
        data="""0;0;----\r
UA11;UA01;Admin1.1\r
UA22;UA02;Admin2.1\r
UA33;UA03;Admin3.1\r
""",
    )

    FlexFormFieldFactory(
        flex_form=frm,
        name="admin1",
        required=False,
        field_type=fields.AjaxSelectField,
        advanced={
            "smart": {
                "datasource": opt1.name,
            }
        },
    )
    FlexFormFieldFactory(
        flex_form=frm,
        name="admin2",
        required=False,
        field_type=fields.AjaxSelectField,
        advanced={
            "smart": {
                "parent_datasource": opt1.name,
                "datasource": opt2.name,
            }
        },
    )

    return RegistrationFactory(
        name="registration #3",
        flex_form=frm,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


@pytest.fixture
def records(registration):
    return RecordFactory.create_batch(1000, registration=registration)


def test_changelist(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_changelist")
    browser.login()
    browser.open(url)
    browser.click("details[data-filter-title='active'] ul li a:contains('Yes')")
    browser.click("details[data-filter-title='active'] ul li a:contains('No')")
    browser.click("details[data-filter-title='active'] ul li a:contains('All')")
    browser.select2_select("ac_project__organization", registration.organization.name)
    browser.select2_select("ac_project", registration.project.name)


def test_menu_admin(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    browser.login()
    browser.open(url)
    browser.select_option_by_text("#btn-admin", "James Editor")
    assert browser.is_text_visible("JAMESPath Editor", selector="#content")
    browser.click_link_text(registration.name)

    browser.select_option_by_text("#btn-admin", "Inspect")
    assert browser.is_text_visible("Inspect Registration", selector="#content")
    browser.click_link_text(registration.name)


def test_menu_admin_create_custom_template(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    browser.login()
    browser.open(url)
    browser.select_option_by_text("#btn-admin", "Create Custom Template")
    browser.select_option_by_text("#id_locale", "Any Language")
    browser.click("input[value=Create]")
    assert browser.is_text_visible("successfully created", selector="html")
    browser.click_link_text("Edit")
    assert browser.is_text_visible("Change template", selector="#content")


def test_menu_admin_clone(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    browser.login()
    browser.open(url)
    browser.select_option_by_text("#btn-admin", "Clone")
    assert browser.is_text_visible("Clone Registration", selector="#content")

    browser.type("input[name=title]", "Cloned Registration")
    browser.click("input[type=submit]")
    assert browser.is_text_visible("Inspect Registration", selector="#content")
    assert browser.get_text("ul.messagelist") == "Registration Successfully Cloned."

    cloned: Registration = Registration.objects.filter(title="Cloned Registration").first()
    assert cloned
    assert cloned.flex_form == registration.flex_form


def test_menu_admin_clone_deep(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    browser.login()
    browser.open(url)
    browser.select_option_by_text("#btn-admin", "Clone")
    assert browser.is_text_visible("Clone Registration", selector="#content")

    browser.type("input[name=title]", "Cloned Registration")
    browser.click("input[name=deep]")
    browser.click("input[type=submit]")
    assert browser.is_text_visible("Inspect Registration", selector="#content")
    assert browser.get_text("ul.messagelist") == "Registration Successfully Cloned."

    cloned: Registration = Registration.objects.filter(title="Cloned Registration").first()
    assert cloned
    assert cloned.flex_form != registration.flex_form


def test_menu_admin_debug(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    browser.login()
    browser.open(url)
    browser.select_option_by_text("#btn-admin", "Debug")
    assert browser.is_text_visible("Debug Registration", selector="#content")
    browser.click("input[type=submit]")


def test_menu_data_charts(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    browser.login()
    browser.open(url)
    browser.select_option_by_text("#btn-data", "Charts")
    assert browser.is_text_visible(registration.name, selector=".breadcrumbs")


def test_menu_data_inspect_data(mock_state, browser: AuroraTestBrowser, records: list[Record]):
    registration = records[0].registration
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    with mock.patch("aurora.registration.admin.registration.is_root", return_value=True):
        browser.login()
        browser.open(url)
        browser.select_option_by_text("#btn-data", "Inspect Data")
        browser.type("#date_start", records[0].timestamp.strftime("%Y-%m-%d"))
        browser.type("#date_end", records[0].timestamp.strftime("%Y-%m-%d"))
        browser.click("#refresh")


def test_menu_encryption_symmetric(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    with mock.patch("aurora.registration.admin.registration.is_root", return_value=True):
        browser.login()
        browser.open(url)
        browser.select_option_by_text("#btn-encryption", "Enable Symmetric")
        assert browser.get_text("ul.messagelist") == "Symmetric Encryption Enabled"
        browser.select_option_by_text("#btn-encryption", "Disable Symmetric")
        assert browser.get_text("ul.messagelist") == "Encryption Not Enabled"


def test_menu_encryption_asymmetric(mock_state, browser: AuroraTestBrowser, registration):
    url = reverse("admin:registration_registration_change", args=[registration.pk])
    with mock.patch("aurora.registration.admin.registration.is_root", return_value=True):
        browser.login()
        browser.open(url)
        browser.select_option_by_text("#btn-encryption", "Enable RSA")
        assert browser.get_text("#content h1").startswith("Generate Private/Public Key pair")
        browser.click("input[type=submit][value='Generate'")
        assert browser.get_text("#content h1").startswith("Key Pair Generated")
        browser.click_link_text("Done")
        assert browser.get_text("ul.messagelist") == "RSA Encryption Enabled"
        browser.select_option_by_text("#btn-encryption", "Remove Key")
        browser.click("#btn-remove")
