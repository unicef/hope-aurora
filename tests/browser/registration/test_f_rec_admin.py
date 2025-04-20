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
    return RecordFactory.create_batch(1000, registration=reg)


def test_changelist(mock_state: State, browser: AuroraTestBrowser, records: "list[Record]", settings):
    registration = records[0].registration

    settings.ROOT_TOKEN = "123"
    url = reverse("admin:registration_record_changelist")
    browser.login()
    browser.open(url)
    assert browser.find_text("403 Forbidden", "body")

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
