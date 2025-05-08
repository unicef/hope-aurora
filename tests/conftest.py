import os
import time
import warnings

import pytest
import responses
from coverage.exceptions import CoverageWarning
from django import forms
from django.core.management import call_command
from django.core.files.storage import default_storage

from aurora.core.fields import CompilationTimeField, SmartFileField
from aurora.registration.models import Registration

ALL = {"darwin"}


@pytest.fixture(autouse=True)
def configure_settings(settings):
    warnings.filterwarnings("ignore", category=CoverageWarning)


def pytest_configure(config):
    from cryptography.fernet import Fernet

    os.environ["DEBUG"] = "0"
    os.environ["ADMINS"] = "admin@demo.org"
    os.environ["CAPTCHA_TEST_MODE"] = "true"
    os.environ["CSRF_COOKIE_SECURE"] = "false"
    os.environ["CSRF_TRUSTED_ORIGINS"] = "http://testserver"
    os.environ["FRONT_DOOR_ENABLED"] = "false"
    os.environ["SECURE_SSL_REDIRECT"] = "false"
    os.environ["SESSION_COOKIE_DOMAIN"] = "http://testserver/"
    os.environ["SESSION_COOKIE_SECURE"] = "false"
    os.environ["SOCIAL_AUTH_REDIRECT_IS_HTTPS"] = "false"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOGGING_HANDLERS"] = "null"
    os.environ["AZURE_CLIENT_SECRET"] = "secret"
    os.environ["AZURE_CLIENT_KEY"] = "key"
    from django.conf import global_settings, settings

    settings.STORAGES = global_settings.STORAGES
    settings.FERNET_KEY = Fernet.generate_key()
    settings.CAPTCHA_TEST_MODE = True
    settings.SESSION_COOKIE_SECURE = False
    settings.DJANGO_ADMIN_URL = "admin/"
    settings.CACHE_PREFIX = str(time.time())
    settings.SOCIAL_AUTH_RESOURCE = "https://graph.microsoft.com"
    settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY = "key"
    settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET = "secret"


@pytest.fixture
def simple_form(db):
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
def complex_form():
    from aurora.core.models import Validator

    v1, __ = Validator.objects.get_or_create(
        name="length_2_8",
        defaults={
            "active": True,
            "target": Validator.FIELD,
            "code": "value.length>1 && value.length<=8 ? true:'String size 1 to 8';",
        },
    )
    from testutils.factories import FormFactory

    hh = FormFactory(name="Form1")

    hh.fields.get_or_create(
        label="Family Name",
        defaults={"field_type": forms.CharField, "required": True, "validator": v1},
    )

    ind = FormFactory(name="Form2", project=hh.project)

    ind.fields.create(
        label="First Name",
        field_type=forms.CharField,
        required=True,
        validator=v1,
    )
    ind.fields.create(
        label="Last Name",
        field_type=forms.CharField,
        required=True,
        validator=v1,
    )
    ind.fields.create(label="Date Of Birth", field_type=forms.DateField, required=True)

    ind.fields.create(label="Image", field_type=SmartFileField, required=False)
    ind.fields.create(label="File", field_type=SmartFileField, required=False)
    hh.add_formset(ind, min_num=0)
    return hh


@pytest.fixture
def mock_storage(monkeypatch):
    """Mocks the backend storage system by not actually accessing media"""

    def clean_name(name):
        return os.path.splitext(os.path.basename(name))[0]

    def _mock_save(instance, name, content):
        setattr(instance, f"mock_{clean_name(name)}_exists", True)
        return str(name).replace("\\", "/")

    def _mock_delete(instance, name):
        setattr(instance, f"mock_{clean_name(name)}_exists", False)

    def _mock_exists(instance, name):
        return getattr(instance, f"mock_{clean_name(name)}_exists", False)

    monkeypatch.setattr(default_storage, "_save", _mock_save)
    monkeypatch.setattr(default_storage, "delete", _mock_delete)
    monkeypatch.setattr(default_storage, "exists", _mock_exists)


@pytest.fixture
def user(db):
    from testutils.factories import UserFactory

    user = UserFactory()
    user._password = "password"
    return user


@pytest.fixture
def staff_user():
    from testutils.factories import UserFactory

    return UserFactory(is_staff=True)


class EnhRequestsMock(responses.RequestsMock):
    def __init__(self, *args, **kwargs):
        self.bc_prefix = kwargs.pop("bc_prefix", None)
        super().__init__(*args, **kwargs)


@pytest.fixture
def mocked_responses():
    with EnhRequestsMock() as rsps:
        yield rsps


@pytest.fixture
def health_registration(db):
    """
    Loads data from 'custom.json' fixture and returns the
    'Country1 Health Registration' Registration object.
    """
    call_command("loaddata", "tests/fixtures/custom.json")
    try:
        return Registration.objects.get(name="Country1 Health Registration")
    except Registration.DoesNotExist:
        pytest.fail(
            "The 'Country1 Health Registration' was not found after loading 'tests/fixtures/custom.json'. "
            "Please ensure the 'name' field in the JSON matches exactly."
        )
