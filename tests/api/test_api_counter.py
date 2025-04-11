from typing import TYPE_CHECKING
from unittest import mock

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from aurora.registration.models import Registration

    class TestRegistration(Registration):
        _private_pem: bytes


@pytest.fixture
def counter(db) -> "TestRegistration":
    from testutils.factories import CounterFactory

    return CounterFactory()


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_counter_list(counter, client):
    res = client.get("/api/counter/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_counter_detail(counter, client):
    res = client.get(f"/api/counter/{counter.pk}/", format="json")
    assert res.status_code == 200


def test_counter_refresh(counter, client):
    with mock.patch("aurora.api.viewsets.counter.ScopedRateThrottle2.rate", "1000/day"):
        res = client.get("/api/counter/refresh/", format="json")
        assert res.status_code == 200
        assert res.json()
    with mock.patch("aurora.api.viewsets.counter.ScopedRateThrottle2.rate", "1/day"):
        res = client.get("/api/counter/refresh/", format="json")
        assert res.status_code == 429
