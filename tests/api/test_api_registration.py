from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import RecordFactory, TokenProxyFactory

if TYPE_CHECKING:
    from aurora.registration.models import Registration

    class TestRegistration(Registration):
        _private_pem: bytes


@pytest.fixture
def registration(simple_form) -> "TestRegistration":
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(name="registration #1", flex_form=simple_form, intro="intro", footer="footer")
    RecordFactory(registration=reg)
    return reg


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_registration_list(registration: "TestRegistration", client):
    res = client.get("/api/registration/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_detail(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_metadata(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/metadata/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_records(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/records/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_csv(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/csv/")
    assert res.status_code == 200

    res = client.get(f"/api/registration/{registration.pk}/csv/?download=1", format="json")
    assert res.status_code == 200
