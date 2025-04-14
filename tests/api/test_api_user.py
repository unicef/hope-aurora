from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()


@pytest.fixture
def user(db) -> "User":
    from testutils.factories import UserFactory

    return UserFactory()


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_user_list(user: "User", client):
    res = client.get("/api/user/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_user_detail(user: "User", client):
    res = client.get(f"/api/user/{user.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_user_me(user: "User", client):
    res = client.get("/api/user/me/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_user_anon(user: "User", client):
    client.credentials(HTTP_AUTHORIZATION="")
    res = client.get("/api/user/me/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_user_admin(admin_user: "User", client):
    client.login(username=admin_user.username, password="password")
    res = client.get("/api/user/me/", format="json")
    assert res.status_code == 200
    assert res.json()
