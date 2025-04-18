import time
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from testutils.factories import FlexFormFieldFactory, FormFactory, OptionSetFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
from aurora.registration.models import Record

if TYPE_CHECKING:
    from aurora.core.models import OptionSet

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


def test_linked_ajax(mock_state, browser: AuroraTestBrowser, registration):
    url = registration.get_absolute_url()
    browser.open(url)
    browser.wait_for_element_not_visible("#loading")
    browser.select2_select("id_admin1", "Admin1")
    time.sleep(0.3)
    browser.select2_select("id_admin2", "Admin1.1")

    browser.select2_select("id_admin1", "Admin2")
    time.sleep(0.3)
    browser.select2_select("id_admin2", "Admin2.1")

    browser.click("input[name=_save_form]")
    reg_id = browser.get_text("#registration-id")
    assert Record.objects.filter(id=reg_id.split("/")[1])
