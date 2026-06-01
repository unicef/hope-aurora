from types import SimpleNamespace

import pytest
from requests import HTTPError

from aurora.security.microsoft_graph import MicrosoftGraphAPI
from aurora.security.microsoft_graph import MicrosoftGraphAPIError


def _response(status_code=200, payload=None, content=b""):
    payload = payload or {}
    return SimpleNamespace(
        status_code=status_code,
        content=content,
        json=lambda: payload,
    )


def test_get_token_success(monkeypatch):
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY",
        "client-id",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET",
        "client-secret",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.requests.post",
        lambda *_a, **_k: _response(payload={"access_token": "tok-1"}),
    )

    api = MicrosoftGraphAPI()
    assert api.get_token() == "tok-1"


def test_get_token_missing_credentials_raises(monkeypatch):
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY",
        "",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET",
        "",
    )
    api = MicrosoftGraphAPI()
    with pytest.raises(MicrosoftGraphAPIError, match="Configure AZURE_CLIENT_ID"):
        api.get_token()


def test_get_token_non_200_raises(monkeypatch):
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY",
        "client-id",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET",
        "client-secret",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.requests.post",
        lambda *_a, **_k: _response(status_code=401, content=b"unauthorized"),
    )
    api = MicrosoftGraphAPI()
    with pytest.raises(MicrosoftGraphAPIError, match="Unable to fetch token from Azure."):
        api.get_token()


def test_get_results_http_error_bubbles(monkeypatch):
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY",
        "client-id",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET",
        "client-secret",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.requests.post",
        lambda *_a, **_k: _response(payload={"access_token": "tok-1"}),
    )

    class _BadResponse:
        @staticmethod
        def raise_for_status():
            raise HTTPError("bad")

        @staticmethod
        def json():
            return {}

    monkeypatch.setattr(
        "aurora.security.microsoft_graph.requests.get",
        lambda *_a, **_k: _BadResponse(),
    )
    api = MicrosoftGraphAPI()
    with pytest.raises(HTTPError):
        api._get_results("https://example")


def test_get_user_data_paths(monkeypatch):
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY",
        "client-id",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET",
        "client-secret",
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.requests.post",
        lambda *_a, **_k: _response(payload={"access_token": "tok-1"}),
    )
    monkeypatch.setattr(
        "aurora.security.microsoft_graph.settings.SOCIAL_AUTH_RESOURCE",
        "https://graph.example",
    )
    api = MicrosoftGraphAPI()

    monkeypatch.setattr(api, "_get_results", lambda q: {"id": "u1", "q": q})
    by_uuid = api.get_user_data(uuid="abc")
    assert by_uuid["id"] == "u1"
    assert by_uuid["q"].endswith("/users/abc")

    monkeypatch.setattr(api, "_get_results", lambda _q: {"value": [{"mail": "x@example.org"}]})
    by_email = api.get_user_data(email="x@example.org")
    assert by_email["mail"] == "x@example.org"

    with pytest.raises(MicrosoftGraphAPIError, match="must provide"):
        api.get_user_data()

    monkeypatch.setattr(api, "_get_results", lambda _q: {"value": []})
    with pytest.raises(Exception, match="User not found"):
        api.get_user_data(email="missing@example.org")
