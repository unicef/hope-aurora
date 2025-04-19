from unittest.mock import Mock

import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from testutils.factories import FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields

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
def registration() -> "Registration":
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    frm.fields.get_or_create(label="Name", required=True, defaults={"field_type": fields.CharField})
    frm.fields.get_or_create(label="Date Of Birth", required=True, defaults={"field_type": fields.DateField})

    return RegistrationFactory(name="registration #3", flex_form=frm, encrypt_data=False)


@pytest.mark.xdist_group("translate")
def test_export_translate(mock_state, browser: AuroraTestBrowser, registration):
    url_list = reverse("admin:registration_registration_changelist")
    url_detail = reverse("admin:registration_registration_change", args=[registration.pk])

    browser.login()
    browser.click(f"tr th a[href='{url_list}']")
    browser.click(f"tr th a[href='{url_detail}']")
    browser.click("select#btn-admin")
    browser.select_option_by_text("select#btn-admin", "Export translation file")
    browser.select_option_by_value("select#id_locale", "it-it")
    browser.click("input[type=submit][name=create]")
    browser.click("input#select_all")
    browser.click("input[type=submit][name=export]")

    exported = browser.get_browser_downloads_folder()
    time.sleep(1)
    assert len(exported)
    assert Path(browser.get_path_of_downloaded_file(exported[0])).exists()


@pytest.mark.xdist_group("translate")
def test_import_translate(mock_state, browser: AuroraTestBrowser, registration):
    url_list = reverse("admin:i18n_message_changelist")
    browser.login()
    browser.click(f"tr th a[href='{url_list}']")
    browser.click("#btn-import_translations")
    browser.select_option_by_value("select#id_locale", "it-it")
    browser.select_option_by_value("select#id_csv-delimiter", ",")

    file_path = "tests/data/it_translations.csv"
    browser.choose_file('input[type="file"]', file_path)
    browser.click("input#import[type=submit]")

    browser.click("input#save")
    time.sleep(0.3)
    assert browser.get_text("ul.messagelist") == "Messages processed: Processed: 5, Selected: 5, Created: 5, Updated: 0"
