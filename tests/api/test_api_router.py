from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from aurora.registration.models import Registration

    class TestRegistration(Registration):
        _private_pem: bytes


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def anonymous_client(db):
    return APIClient()


def test_router_auth(client):
    res = client.get("/api/", format="json")
    assert res.status_code == 200


def test_router_denied(anonymous_client):
    anonymous_client.credentials(HTTP_AUTHORIZATION="")
    res = anonymous_client.get("/api/", format="json")
    assert res.status_code == 401


def test_router_no_auth(anonymous_client):
    res = anonymous_client.get("/api/", format="json")
    assert res.status_code == 401
