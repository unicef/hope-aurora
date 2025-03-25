import os
from typing import TYPE_CHECKING, Any

import pytest
import sys
from django import forms
from django.conf import settings as django_settings
from django.core.files.storage import default_storage

from aurora.core.fields import CompilationTimeField, SmartFileField

if TYPE_CHECKING:
    from django.contrib.auth.models import User
    from aurora.core.models import FlexForm
    from aurora.registration.models import Registration

ALL = set("darwin".split())

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../extras")))


@pytest.fixture(autouse=True)
def configure_settings(settings: django_settings) -> None:
    from cryptography.fernet import Fernet

    settings.FERNET_KEY = Fernet.generate_key()
    settings.ADMINS = ["admin@demo.org"]
    settings.CAPTCHA_TEST_MODE = True


def pytest_configure(config: Any) -> None:
    os.environ["DEBUG"] = "0"
    os.environ["ADMINS"] = "admin@demo.org"
    os.environ["CAPTCHA_TEST_MODE"] = "true"
    os.environ["CSRF_COOKIE_SECURE"] = "false"
    os.environ["CSRF_TRUSTED_ORIGINS"] = "http://testserver"
    os.environ["SECURE_SSL_REDIRECT"] = "false"
    os.environ["SESSION_COOKIE_DOMAIN"] = "http://testserver/"
    os.environ["SESSION_COOKIE_SECURE"] = "false"
    os.environ["SOCIAL_AUTH_REDIRECT_IS_HTTPS"] = "false"
    os.environ["LOG_LEVEL"] = "CRITICAL"
    os.environ["LOGGING_HANDLERS"] = "null"

    from django.conf import global_settings, settings

    settings.STORAGES = global_settings.STORAGES


@pytest.fixture
def simple_form(db: Any) -> "FlexForm":
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
    frm.fields.get_or_create(label="First Name", defaults={"field_type": forms.CharField(required=False)})
    frm.fields.get_or_create(
        label="Last Name",
        defaults={
            "field_type": forms.CharField,
            "required": True,
            "validator": v2,
            "advanced": {"smart": {"index": 1}},
        },
    )
    frm.fields.get_or_create(label="Image", defaults={"field_type": forms.ImageField(required=False)})
    frm.fields.get_or_create(label="File", defaults={"field_type": forms.FileField(required=False)})
    frm.fields.get_or_create(label="index_no", defaults={"field_type": forms.CharField(max_length=100, required=False)})
    frm.fields.get_or_create(label="Name", defaults={"field_type": forms.CharField(required=False)})
    return frm


@pytest.fixture
def complex_form(db: Any) -> "FlexForm":
    from aurora.core.models import Validator
    from testutils.factories import FormFactory, FormSetFactory

    v1, __ = Validator.objects.get_or_create(
        name="length_2_8",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>1 && value.length<=8 ? true:'String size 1 to 8';",
        },
    )

    hh = FormFactory(name="Form1")
    hh.fields.get_or_create(
        label="Family Name",
        defaults={"field_type": forms.CharField(max_length=100, required=True), "required": True, "validator": v1},
    )
    ind = FormFactory(name="Form2", project=hh.project)
    ind.fields.create(
        label="First Name",
        field_type=forms.CharField(max_length=100, required=True),
        validator=v1,
    )
    ind.fields.create(
        label="Last Name",
        field_type=forms.CharField(max_length=100, required=True),
        validator=v1,
    )
    ind.fields.create(
        label="Date Of Birth",
        field_type=forms.DateField(required=True),
    )
    ind.fields.create(
        label="Image",
        field_type=SmartFileField(required=False),
    )
    ind.fields.create(
        label="File",
        field_type=SmartFileField(required=False),
    )

    FormSetFactory(parent=hh, flex_form=ind, name="form2s")

    return hh


@pytest.fixture
def mock_storage(monkeypatch: Any) -> None:
    """Mocks the backend storage system by not actually accessing media"""

    def clean_name(name: str) -> str:
        return os.path.splitext(os.path.basename(name))[0]

    def _mock_save(instance: Any, name: str, content: Any) -> str:
        setattr(instance, f"mock_{clean_name(name)}_exists", True)
        return str(name).replace("\\", "/")

    def _mock_delete(instance: Any, name: str) -> None:
        setattr(instance, f"mock_{clean_name(name)}_exists", False)

    def _mock_exists(instance: Any, name: str) -> bool:
        return getattr(instance, f"mock_{clean_name(name)}_exists", False)

    monkeypatch.setattr(default_storage, "_save", _mock_save)
    monkeypatch.setattr(default_storage, "delete", _mock_delete)
    monkeypatch.setattr(default_storage, "exists", _mock_exists)


@pytest.fixture
def user(db: Any) -> "User":
    from testutils.factories import UserFactory

    return UserFactory()


@pytest.fixture
def staff_user(db: Any) -> "User":
    from testutils.factories import UserFactory

    return UserFactory(is_staff=True)


@pytest.fixture
def simple_registration(simple_form: "FlexForm") -> "Registration":
    """Fixture to create a Registration instance with a simple_form flex_form."""
    from testutils.factories import ProjectFactory, RegistrationFactory

    project = ProjectFactory()
    return RegistrationFactory(flex_form=simple_form, project=project)


@pytest.fixture
def complex_registration(complex_form: "FlexForm") -> "Registration":
    """Fixture to create a Registration instance with a givcomplex_formen flex_form."""
    from testutils.factories import ProjectFactory, RegistrationFactory

    project = ProjectFactory()
    return RegistrationFactory(flex_form=complex_form, project=project)

