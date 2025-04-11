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


def test_system_info(client):
    res = client.get("/api/sys/", format="json")
    assert res.status_code == 200
    assert res.json()
