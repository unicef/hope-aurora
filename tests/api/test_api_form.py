from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from aurora.registration.models import FlexForm


@pytest.fixture
def form(simple_form) -> "FlexForm":
    return simple_form


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_form_list(form: "FlexForm", client):
    res = client.get("/api/form/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_form_detail(form: "FlexForm", client):
    res = client.get(f"/api/form/{form.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()
