from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from aurora.registration.models import Record


@pytest.fixture
def record(db) -> "Record":
    from testutils.factories import RecordFactory

    return RecordFactory()


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_record_list(record: "Record", client):
    res = client.get("/api/record/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_record_detail(record: "Record", client):
    res = client.get(f"/api/record/{record.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_record_metadata(record: "Record", client):
    res = client.get(f"/api/record/{record.pk}/metadata/", format="json")
    assert res.status_code == 200
    assert res.json()
