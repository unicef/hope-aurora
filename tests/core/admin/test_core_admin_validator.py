from typing import TYPE_CHECKING
from unittest import mock

import pytest
from django.urls import reverse

from aurora.registration.models import Registration

if TYPE_CHECKING:
    from aurora.core.models import FlexForm


@pytest.fixture
def form_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Form", target=Validator.FORM, active=True, code=code)


@pytest.fixture
def formset_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Formset", target=Validator.FORMSET, active=True, code=code)


@pytest.fixture
def field_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Field", target=Validator.FIELD, active=True, code=code)


@pytest.fixture
def module_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Module", target=Validator.MODULE, active=True, code=code)


@pytest.fixture
def script_validator(db):
    from testutils.factories import Validator, ValidatorFactory

    code = """true"""
    return ValidatorFactory(name="Validator Script", target=Validator.SCRIPT, active=True, code=code)


@pytest.fixture
def flex_form(db, form_validator) -> "FlexForm":
    from testutils.factories import FormFactory

    return FormFactory(name="Form1", validator=form_validator)


@pytest.fixture
def registration(flex_form, module_validator) -> Registration:
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=flex_form,
        validator=module_validator,
        encrypt_data=False,
        export_allowed=True,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


@pytest.fixture
def data(form_validator, formset_validator, field_validator, module_validator, script_validator, registration):
    pass


@pytest.fixture
def app(django_app_factory, db):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app


def test_validator_changelist(app, data):
    url = reverse("admin:core_validator_changelist")
    res = app.get(url)
    assert res.status_code == 200


@pytest.mark.parametrize("validator", ["form_validator", "field_validator", "module_validator", "script_validator"])
def test_validator_test(request, app, validator):
    validator = request.getfixturevalue(validator)

    url = reverse("admin:core_validator_test", args=[validator.id])
    with mock.patch("aurora.security.admin.is_root", return_value=True):
        res = app.get(url)
        form = res.forms["test-form"]
        res = form.submit()
        assert res.status_code == 200
        res = form.submit()
        assert res.status_code == 200


def test_validator_invalid(request, app, form_validator):
    url = reverse("admin:core_validator_test", args=[form_validator.id])
    with mock.patch("aurora.security.admin.is_root", return_value=True):
        res = app.get(url)
        form = res.forms["test-form"]
        form["code"] = "-"
        assert res.status_code == 200
