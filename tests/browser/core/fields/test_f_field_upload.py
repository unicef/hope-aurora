import base64
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from testutils.factories import FlexFormFieldFactory, FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields

if TYPE_CHECKING:
    from aurora.registration.models import Record, Registration

pytestmark = pytest.mark.selenium


@pytest.fixture
def registration():
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    FlexFormFieldFactory(flex_form=frm, name="file", required=True, field_type=fields.SmartFileField)
    return RegistrationFactory(name="registration #3", flex_form=frm, encrypt_data=False)


def test_upload_file(mock_state, browser: AuroraTestBrowser, registration: "Registration"):
    record: Record
    url = registration.get_absolute_url()
    browser.open(url)
    browser.wait_for_element_not_visible("#loading")
    browser.show_file_choosers()
    file_path = Path(__file__)
    browser.choose_file('input[type="file"]', file_path)
    browser.click("input[type=submit]")
    time.sleep(0.3)
    assert (record := registration.record_set.first())
    assert base64.b64decode(record.data["file"]).decode() == Path(__file__).read_text()
