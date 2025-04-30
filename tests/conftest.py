import os
import time
import warnings
from pathlib import Path

import pytest
from coverage.exceptions import CoverageWarning

ALL = {"darwin"}


@pytest.fixture(autouse=True)
def configure_settings(settings):
    warnings.filterwarnings("ignore", category=CoverageWarning)


def pytest_addoption(parser):
    parser.addoption("--no-stack", action="store_true", default=False)


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
    os.environ["DJANGO_SETTINGS_MODULE"] = "aurora.config.settings"

    os.environ["DATABASE_URL"] = "postgres://postgres:@127.0.0.1:15432/aurora"
    os.environ["CACHE_DEFAULT"] = "redis://127.0.0.1:16379/2"

    from django.conf import global_settings, settings

    settings.STORAGES = global_settings.STORAGES
    settings.FERNET_KEY = Fernet.generate_key()
    settings.CAPTCHA_TEST_MODE = True
    settings.SESSION_COOKIE_SECURE = False
    settings.DJANGO_ADMIN_URL = "admin/"
    settings.CACHE_PREFIX = str(time.time())


@pytest.fixture(scope="session")
def docker_compose_command() -> str:
    return "docker compose"


@pytest.fixture(scope="session")
def docker_setup():
    return ["up -d"]


@pytest.fixture(scope="session")
def docker_teardown():
    return ["rm -fsv"]


@pytest.fixture(scope="session")
def docker_compose_file():
    return str(Path(__file__).parent / "compose.yml")


@pytest.fixture(scope="session")
def docker_compose_project_name() -> str:
    return "aurora-test-stack"


def is_responsive(address, port):
    try:
        import socket

        sock = socket.socket()
        sock.connect((address, port))
        return True
    except ConnectionError:
        return False


@pytest.fixture(scope="session", autouse=True)
def services(docker_ip, docker_services):
    port = docker_services.port_for("db", 5432)
    docker_services.wait_until_responsive(timeout=30.0, pause=0.1, check=lambda: is_responsive(docker_ip, port))


@pytest.fixture
def simple_form(db):
    from aurora.core.cache import cache
    from aurora.core.models import Validator
    from django import forms
    from aurora.core.fields import CompilationTimeField

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
    from django import forms
    from aurora.core.fields import SmartFileField

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
    from django.core.files.storage import default_storage

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
