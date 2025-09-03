from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.urls import reverse

if TYPE_CHECKING:
    from aurora.core.models import FlexForm


@pytest.fixture
def form_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Form", target=Validator.FORM, active=True, code=code)


@pytest.fixture
def flex_form(db, form_validator) -> "FlexForm":
    from testutils.factories import FormFactory

    return FormFactory(name="Form1", validator=form_validator)


@pytest.fixture
def app(django_app_factory, db):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app


def test_flexform_changelist(app, flex_form):
    url = reverse("admin:core_flexform_changelist")
    res = app.get(url)
    assert res.status_code == 200


def test_flexform_editor(request, app, flex_form):
    url = reverse("admin:core_flexform_form_editor", args=[flex_form.id])
    with mock.patch("aurora.security.admin.is_root", return_value=True):
        app.get(url)
