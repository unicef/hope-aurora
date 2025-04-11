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


def test_organization_list(registration: "TestRegistration", client):
    res = client.get("/api/organization/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_organization_detail(registration: "TestRegistration", client):
    res = client.get(f"/api/organization/{registration.project.organization.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_organization_projects(registration: "TestRegistration", client):
    res = client.get(f"/api/organization/{registration.project.organization.pk}/projects/", format="json")
    assert res.status_code == 200
    assert res.json()
