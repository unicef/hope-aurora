import json

import pytest
from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from rest_framework.test import APIClient
from testutils.factories import RecordFactory, RegistrationFactory, TokenProxyFactory

from aurora.api.renderers import EncryptedJSONRenderer


@pytest.fixture
def encryption_key():
    return Fernet.generate_key()


@pytest.fixture
def renderer():
    return EncryptedJSONRenderer()


@pytest.fixture
def registration(simple_form):
    reg = RegistrationFactory(flex_form=simple_form)
    RecordFactory.create_batch(size=3, registration=reg)
    return reg


@pytest.fixture
def client(admin_user):
    api_client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    api_client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return api_client


def test_renderer_media_type(renderer):
    assert renderer.media_type == "application/encrypted+json"


def test_renderer_format(renderer):
    assert renderer.format == "encrypted_json"


def test_renderer_encrypts_output(renderer, encryption_key, settings):
    settings.AURORA_PAYLOAD_ENCRYPTION_KEY = encryption_key
    data = {"results": [{"pk": 1, "fields": {"name": "Alice"}}], "count": 1, "next": None}

    output: bytes = renderer.render(data)

    outer = json.loads(output)
    assert "payload" in outer
    assert isinstance(outer["payload"], str)


def test_renderer_round_trip(renderer, encryption_key, settings):
    settings.AURORA_PAYLOAD_ENCRYPTION_KEY = encryption_key
    original = {"results": [{"pk": 42, "fields": {"foo": "bar"}}], "count": 1, "next": None}

    output: bytes = renderer.render(original)

    outer = json.loads(output)
    token = outer["payload"].encode("utf-8")
    plaintext = Fernet(encryption_key).decrypt(token)
    recovered = json.loads(plaintext)
    assert recovered == original


def test_renderer_raises_when_key_not_configured(renderer, settings):
    settings.AURORA_PAYLOAD_ENCRYPTION_KEY = ""

    with pytest.raises(ImproperlyConfigured, match="AURORA_PAYLOAD_ENCRYPTION_KEY"):
        renderer.render({"results": []})


def test_renderer_raises_when_key_attribute_absent(renderer, settings):
    if hasattr(settings, "AURORA_PAYLOAD_ENCRYPTION_KEY"):
        delattr(settings, "AURORA_PAYLOAD_ENCRYPTION_KEY")

    with pytest.raises(ImproperlyConfigured, match="AURORA_PAYLOAD_ENCRYPTION_KEY"):
        renderer.render({"results": []})


def test_renderer_output_is_bytes(renderer, encryption_key, settings):
    settings.AURORA_PAYLOAD_ENCRYPTION_KEY = encryption_key

    output = renderer.render([1, 2, 3])

    assert isinstance(output, bytes)


@pytest.mark.django_db
def test_records_endpoint_returns_encrypted_payload(registration, client, settings, encryption_key):
    """Integration: the records endpoint honours Accept: application/encrypted+json."""
    settings.AURORA_PAYLOAD_ENCRYPTION_KEY = encryption_key

    res = client.get(
        f"/api/registration/{registration.pk}/records/",
        HTTP_ACCEPT="application/encrypted+json",
    )

    assert res.status_code == 200
    assert "application/encrypted+json" in res.headers.get("Content-Type", "")
    outer = json.loads(res.content)
    assert "payload" in outer

    token = outer["payload"].encode("utf-8")
    plaintext = Fernet(encryption_key).decrypt(token)
    data = json.loads(plaintext)
    assert "results" in data


@pytest.mark.django_db
def test_records_endpoint_plain_json_without_accept_header(registration, client, settings, encryption_key):
    """Without encrypted Accept header the response is plain JSON (backward compat)."""
    settings.AURORA_PAYLOAD_ENCRYPTION_KEY = encryption_key

    res = client.get(f"/api/registration/{registration.pk}/records/", format="json")

    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "payload" not in data
