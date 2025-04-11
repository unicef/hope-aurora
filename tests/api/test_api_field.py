from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from aurora.core.models import FlexFormField

if TYPE_CHECKING:
    from aurora.registration.models import Registration

    class TestRegistration(Registration):
        _private_pem: bytes


@pytest.fixture
def field(simple_form) -> "FlexFormField":
    from testutils.factories import FlexFormFieldFactory

    return FlexFormFieldFactory()


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_organization_list(field: "FlexFormField", client):
    res = client.get("/api/field/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_organization_detail(field: "FlexFormField", client):
    res = client.get(f"/api/field/{field.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()
