from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from aurora.registration.models import Validator


@pytest.fixture
def validator(db) -> "Validator":
    from testutils.factories import ValidatorFactory

    return ValidatorFactory(code="")


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_validator_list(validator: "Validator", client):
    res = client.get("/api/validator/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_validator_detail(validator: "Validator", client):
    res = client.get(f"/api/validator/{validator.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_validator_validator(validator: "Validator", client):
    res = client.get(f"/api/validator/{validator.pk}/validator/", format="json")
    assert res.status_code == 200


def test_validator_script(validator: "Validator", client):
    res = client.get(f"/api/validator/{validator.pk}/script/", format="json")
    assert res.status_code == 200
