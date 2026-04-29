from typing import TYPE_CHECKING
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIClient
from testutils.factories import RecordFactory, TokenProxyFactory

from aurora.api.viewsets.registration import RegistrationViewSet

if TYPE_CHECKING:
    from aurora.registration.models import Registration

    class TestRegistration(Registration):
        _private_pem: bytes


@pytest.fixture
def registration(simple_form) -> "TestRegistration":
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(name="registration #1", flex_form=simple_form, intro="intro", footer="footer")
    RecordFactory.create_batch(size=102, registration=reg)
    return reg


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_registration_list(registration: "TestRegistration", client):
    res = client.get("/api/registration/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_detail(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_metadata(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/metadata/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_records(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/records/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_registration_records_permission_denied_direct_call(rf):
    request = rf.get("/api/registration/1/records/")
    request.user = SimpleNamespace(has_perm=lambda *_args, **_kwargs: False)
    view = RegistrationViewSet()
    view.get_object = lambda: SimpleNamespace(active=True, version=1)

    with pytest.raises(PermissionDenied):
        view.records(request, pk="1")


def test_registration_records_returns_conditional_response(monkeypatch, rf):
    request = rf.get("/api/registration/1/records/")
    request.user = SimpleNamespace(has_perm=lambda *_args, **_kwargs: True)
    view = RegistrationViewSet()
    view.get_object = lambda: SimpleNamespace(active=True, version=1)

    conditional = SimpleNamespace(headers={}, status_code=304)
    monkeypatch.setattr("aurora.api.viewsets.registration.get_etag", lambda *_a, **_k: "etag")
    monkeypatch.setattr("aurora.api.viewsets.registration.get_conditional_response", lambda *_a, **_k: conditional)

    response = view.records(request, pk="1")
    assert response.status_code == 304
    assert response.headers["ETag"] == "etag"
    assert response.headers["Cache-Control"] == "private, max-age=120"


def test_registration_records_invalid_serializer_falls_back_to_fields(monkeypatch, rf):
    request = rf.get("/api/registration/1/records/?ser=invalid")
    request.user = SimpleNamespace(has_perm=lambda *_args, **_kwargs: True)
    view = RegistrationViewSet()
    view.get_object = lambda: SimpleNamespace(active=True, version=1)
    view.allowed_serializers = {"fields"}

    class DummySerializer:
        def __init__(self, *_args, **_kwargs):
            self.data = [{"ok": 1}]

    view.RecordSerializerMap = {"fields": DummySerializer}

    queryset = Mock()
    queryset.defer.return_value = queryset
    monkeypatch.setattr("aurora.api.viewsets.registration.Record.objects.filter", lambda **_k: queryset)
    monkeypatch.setattr("aurora.api.viewsets.registration.get_etag", lambda *_a, **_k: "etag")
    monkeypatch.setattr("aurora.api.viewsets.registration.get_conditional_response", lambda *_a, **_k: None)

    class FakeFilter:
        def __init__(self, *_args, **_kwargs):
            self.form = SimpleNamespace(is_valid=lambda: False)

        def filter_queryset(self, qs):
            raise AssertionError("filter_queryset should not be called for invalid filter form")

    monkeypatch.setattr("aurora.api.viewsets.registration.RecordFilter", FakeFilter)
    monkeypatch.setattr(
        "aurora.api.viewsets.registration.RecordPageNumberPagination.paginate_queryset",
        lambda *_a, **_k: None,
    )

    response = view.records(request, pk="1")
    assert response.status_code == 200
    assert response.data == [{"ok": 1}]


def test_registration_records_page_size_is_capped(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/records/?page_size=1000", format="json")
    assert res.status_code == 200
    data = res.json()
    assert len(data["results"]) == 100
    assert data["count"] == 102


def test_registration_records_sets_cache_headers(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/records/", format="json")
    assert res.status_code == 200
    etag = res.headers.get("ETag")
    assert etag
    assert res.headers.get("Cache-Control") == "private, max-age=120"


def test_registration_csv(registration: "TestRegistration", client):
    res = client.get(f"/api/registration/{registration.pk}/csv/")
    assert res.status_code == 200

    res = client.get(f"/api/registration/{registration.pk}/csv/?download=1", format="json")
    assert res.status_code == 200


@pytest.mark.parametrize("serializer", ["", "files", "fields", "full", "storage", "-invalid"])
def test_registration_records_serializer(registration: "TestRegistration", client, serializer: str):
    url = f"/api/registration/{registration.pk}/records/?ser={serializer}"
    res = client.get(url, format="json")
    assert res.status_code == 200
    assert res.json()


@pytest.mark.parametrize("serializer", ["", "files", "fields", "full", "storage", "-invalid"])
def test_registration_records_pages(registration: "TestRegistration", client, serializer: str):
    url = f"/api/registration/{registration.pk}/records/?ser={serializer}&page_size=10&page=2"
    res = client.get(url, format="json")
    assert res.status_code == 200
    assert res.json()
