from unittest.mock import Mock

import pytest
from django import forms
from testutils.selenium import AuroraTestBrowser

from aurora.core.fields import CompilationTimeField
from aurora.registration.models import Record

pytestmark = pytest.mark.selenium


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())
    yield
    state.request = None


@pytest.fixture
def simple_form():
    from aurora.core.cache import cache
    from aurora.core.models import Validator

    cache.clear()

    v1, __ = Validator.objects.update_or_create(
        label="length_1_50",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>1 && value.length<=50 ? true: 'String size 1 to 5'",
        },
    )
    v2, __ = Validator.objects.update_or_create(
        label="length_2_10",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>2 && value.length<=10 ? true: 'String size 2 to 10';",
        },
    )
    from testutils.factories import FormFactory

    frm = FormFactory(name="Form1")
    frm.fields.get_or_create(label="time", defaults={"field_type": CompilationTimeField})
    frm.fields.get_or_create(label="First Name", defaults={"field_type": forms.CharField, "required": True})
    frm.fields.get_or_create(
        label="Last Name",
        defaults={
            "field_type": forms.CharField,
            "required": True,
            "validator": v2,
            "advanced": {"smart": {"index": 1}},
        },
    )
    frm.fields.get_or_create(label="Image", defaults={"field_type": forms.ImageField, "required": False})
    frm.fields.get_or_create(label="File", defaults={"field_type": forms.FileField, "required": False})
    frm.fields.get_or_create(label="index_no", defaults={"field_type": forms.CharField, "required": False})
    return frm


@pytest.fixture
def registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


def test_register(mock_state, browser: AuroraTestBrowser, registration):
    url = registration.get_absolute_url()
    browser.open(url)
    browser.type("input[name=first_name]", "first_name")
    browser.type("input[name=last_name]", "last_name")
    browser.type("input[name=index_no]", "123456")
    browser.click("input[name=_save_form]")
    reg_id = browser.get_text("#registration-id")
    browser.click("a:contains('register another household')")
    assert Record.objects.filter(id=reg_id.split("/")[1])
