from typing import TYPE_CHECKING

import pytest
from django.urls import reverse
from testutils.factories import FlexFormFieldFactory, FormFactory, RegistrationFactory
from testutils.selenium import AuroraTestBrowser

from aurora.core import fields
from aurora.core.models import FlexFormField

if TYPE_CHECKING:
    from aurora.registration.models import FlexForm

pytestmark = pytest.mark.selenium


@pytest.fixture
def flex_form() -> "FlexForm":
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    FlexFormFieldFactory(
        flex_form=frm,
        name="field1",
        required=True,
        advanced={
            **FlexFormField.FLEX_FIELD_DEFAULT_ATTRS,
            "widget": {
                "placeholder": "placeholder_text",
                "extra_classes": "extra-test-class",
            },
            "smart": {
                "hint": "hint text",
                "description": "description text",
            },
        },
        field_type=fields.CharField,
    )
    FlexFormFieldFactory(
        flex_form=frm,
        name="field2",
        required=True,
        advanced={
            **FlexFormField.FLEX_FIELD_DEFAULT_ATTRS,
            "smart": {
                "question": "question text",
            },
        },
        field_type=fields.CharField,
    )
    RegistrationFactory(
        name="registration #3",
        flex_form=frm,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )
    return frm


def test_changelist(mock_state, browser: AuroraTestBrowser, flex_form: "FlexForm") -> None:
    url = reverse("admin:core_flexform_changelist")
    browser.login()
    browser.open(url)
    registration = flex_form.registration_set.first()
    browser.select2_select("ac_project__organization", registration.organization.name)
    browser.select2_select("ac_project", registration.project.name)
    browser.select2_select("ac_registration", registration.name)
