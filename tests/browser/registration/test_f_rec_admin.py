from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.urls import reverse
from faker import Faker
from testutils.factories import RecordFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.state import State

if TYPE_CHECKING:
    from aurora.registration.models import Record

fake = Faker()

pytestmark = pytest.mark.selenium


@pytest.fixture
def records():
    reg = RegistrationFactory()
    return RecordFactory.create_batch(100, files=None, registration=reg)


def test_changelist(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    settings.ROOT_TOKEN = "123"
    url = reverse("admin:registration_record_changelist")
    browser.login()
    browser.open(url)
    assert browser.find_text("403 Forbidden", "body")
    registration = records[0].registration

    with mock.patch("aurora.registration.admin.record.is_root", return_value=True):
        browser.open(url)
        browser.select2_select("ac_registration", registration.name)
        browser.click("details[data-filter-title='Latest [n] hours'] ul li a:contains('30 min')")
        browser.click("details[data-filter-title='Latest [n] hours'] ul li a:contains('All')")
        browser.type("div#timestamp input[name=value]", records[0].timestamp.strftime("%Y-%m-%d"))
        browser.click("div#timestamp a.filter")


def test_change(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    record: Record = records[0]

    settings.ROOT_TOKEN = "123"
    url = reverse("admin:registration_record_change", args=[record.pk])
    browser.login()
    browser.open(url)
    assert browser.find_text("403 Forbidden", "body")

    with mock.patch("aurora.registration.admin.record.is_root", return_value=True):
        browser.open(url)


def test_button_receipt(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    record: Record = records[0]
    browser.login()
    url = reverse("admin:registration_record_change", args=[record.pk])
    with mock.patch("aurora.registration.admin.record.is_root", return_value=True):
        browser.open(url)
        browser.click("#btn-receipt")
        assert browser.get_text("#registration-id") == record.unicef_id


def test_button_preview(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    settings.ROOT_TOKEN = "123"
    settings.FLAGS = {"IS_ROOT": [("boolean", True)]}
    record: Record = records[0]
    url = reverse("admin:registration_record_change", args=[record.pk])
    browser.login()
    browser.open(url)
    browser.click("#btn-preview")
    assert browser.get_text("#content h1") == "Preview "


def test_button_inspect(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    settings.ROOT_TOKEN = "123"
    settings.FLAGS = {"IS_ROOT": [("boolean", True)]}
    record: Record = records[0]
    url = reverse("admin:registration_record_change", args=[record.pk])
    browser.login()
    browser.open(url)
    browser.click("#btn-inspect")
    assert browser.get_text("#content h1") == "Inspect "


def test_button_decrypt(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    settings.ROOT_TOKEN = "123"
    settings.FLAGS = {"IS_ROOT": [("boolean", True)]}
    record: Record = records[0]
    url = reverse("admin:registration_record_change", args=[record.pk])
    browser.login()
    browser.open(url)
    browser.click("#btn-decrypt")
    assert browser.get_text("#content h1") == "To decrypt you need to provide Registration Private Key "
