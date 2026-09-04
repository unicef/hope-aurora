from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import (
    CounterFactory,
    RecordFactory,
    RegistrationFactory,
    TokenProxyFactory,
    ValidatorFactory,
)
from testutils.perms import user_grant_permissions

if TYPE_CHECKING:
    from aurora.security.models import User


@pytest.fixture
def anonymous_client(db):
    return APIClient()


@pytest.fixture
def api_user(db) -> "User":
    from testutils.factories import UserFactory

    return UserFactory()


def make_client(user):
    client = APIClient()
    token = TokenProxyFactory(user=user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def client(api_user):
    return make_client(api_user)


@pytest.fixture
def registration(simple_form):
    reg = RegistrationFactory(name="registration #auth", flex_form=simple_form)
    RecordFactory.create_batch(size=5, registration=reg)
    return reg


@pytest.fixture
def other_registration(simple_form):
    return RegistrationFactory(name="registration #other", flex_form=simple_form)


@pytest.fixture
def validator(db):
    return ValidatorFactory(code="")


@pytest.fixture
def counter(db):
    return CounterFactory()


# ---------------------------------------------------------------------------
# Anonymous users are denied everywhere
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "/api/organization/",
        "/api/project/",
        "/api/registration/",
        "/api/record/",
        "/api/form/",
        "/api/field/",
        "/api/formset/",
        "/api/user/",
        "/api/validator/",
        "/api/counter/",
        "/api/flatpage/",
        "/api/template/",
    ],
)
def test_anonymous_denied_list(url, anonymous_client):
    res = anonymous_client.get(url, format="json")
    assert res.status_code in (401, 403)


@pytest.mark.parametrize(
    "url",
    [
        "/api/organization/1/",
        "/api/project/1/",
        "/api/registration/1/",
        "/api/record/1/",
        "/api/form/1/",
        "/api/field/1/",
        "/api/formset/1/",
        "/api/validator/1/",
        "/api/flatpage/1/",
        "/api/template/1/",
    ],
)
def test_anonymous_denied_detail(url, anonymous_client):
    res = anonymous_client.get(url, format="json")
    assert res.status_code in (401, 403)


def test_anonymous_denied_registration_metadata(anonymous_client, registration):
    res = anonymous_client.get(f"/api/registration/{registration.pk}/metadata/", format="json")
    assert res.status_code in (401, 403)


def test_anonymous_denied_registration_version(anonymous_client, registration):
    res = anonymous_client.get(f"/api/registration/{registration.pk}/version/", format="json")
    assert res.status_code in (401, 403)


def test_anonymous_denied_counter_refresh(anonymous_client, counter):
    res = anonymous_client.get("/api/counter/refresh/", format="json")
    assert res.status_code in (401, 403)


def test_anonymous_denied_sysinfo(anonymous_client):
    res = anonymous_client.get("/api/sys/", format="json")
    assert res.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Form Viewer (no scope) cannot access organization, project or records
# ---------------------------------------------------------------------------


def test_unscoped_user_cannot_view_organizations(registration, client):
    res = client.get("/api/organization/", format="json")
    assert res.status_code == 200
    assert res.json()["results"] == []


def test_unscoped_user_cannot_view_projects(registration, client):
    res = client.get("/api/project/", format="json")
    assert res.status_code == 200
    assert res.json()["results"] == []


def test_unscoped_user_cannot_view_records(registration, client):
    res = client.get("/api/record/", format="json")
    assert res.status_code == 200
    assert res.json()["results"] == []


# ---------------------------------------------------------------------------
# Scoped user can only see objects within scope
# ---------------------------------------------------------------------------


def test_scoped_user_sees_only_own_registration(registration, other_registration, api_user):
    client = make_client(api_user)
    with user_grant_permissions(api_user, "registration.view_registration", registration):
        res = client.get("/api/registration/", format="json")
        assert res.status_code == 200
        results = res.json()["results"]
        assert {r["id"] for r in results} == {registration.pk}

        res = client.get(f"/api/registration/{registration.pk}/", format="json")
        assert res.status_code == 200

        res = client.get(f"/api/registration/{other_registration.pk}/", format="json")
        assert res.status_code == 404


def test_scoped_user_sees_org_project_but_not_others(registration, other_registration, api_user):
    client = make_client(api_user)
    with user_grant_permissions(api_user, "core.view_project", registration):
        res = client.get("/api/project/", format="json")
        assert res.status_code == 200
        ids = [r["id"] for r in res.json()["results"]]
        assert registration.project.pk in ids
        assert other_registration.project.pk not in ids


def test_scoped_user_sees_own_org(registration, other_registration, api_user):
    client = make_client(api_user)
    with user_grant_permissions(api_user, "core.view_organization", registration):
        res = client.get("/api/organization/", format="json")
        assert res.status_code == 200
        ids = [r["id"] for r in res.json()["results"]]
        assert registration.project.organization.pk in ids
        assert other_registration.project.organization.pk != registration.project.organization.pk
        assert other_registration.project.organization.pk not in ids


def test_scoped_user_can_view_records_only_in_scope(registration, other_registration, api_user):
    RecordFactory.create_batch(size=3, registration=other_registration)
    client = make_client(api_user)
    with user_grant_permissions(api_user, "registration.can_view_data", registration):
        res = client.get("/api/record/", format="json")
        assert res.status_code == 200
        results = res.json()["results"]
        assert all(r["registration"] == registration.pk for r in results)


# ---------------------------------------------------------------------------
# Registration data export requires export_data permission
# ---------------------------------------------------------------------------


def test_csv_requires_export_permission(registration, api_user):
    client = make_client(api_user)
    with user_grant_permissions(api_user, "registration.view_registration", registration):
        res = client.get(f"/api/registration/{registration.pk}/csv/")
        assert res.status_code == 403


def test_csv_allowed_with_export_permission(registration, api_user):
    client = make_client(api_user)
    with user_grant_permissions(
        api_user, ["registration.view_registration", "registration.export_data"], registration
    ):
        res = client.get(f"/api/registration/{registration.pk}/csv/?preview=1")
        assert res.status_code == 200


def test_records_requires_can_view_data(registration, api_user):
    client = make_client(api_user)
    with user_grant_permissions(api_user, "registration.view_registration", registration):
        res = client.get(f"/api/registration/{registration.pk}/records/")
        assert res.status_code == 403


def test_records_allowed_with_can_view_data(registration, api_user):
    client = make_client(api_user)
    perms = ["registration.view_registration", "registration.can_view_data"]
    with user_grant_permissions(api_user, perms, registration):
        res = client.get(f"/api/registration/{registration.pk}/records/")
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# Admin-only endpoints: users, validators, counters, flatpages, templates
# ---------------------------------------------------------------------------


def test_non_staff_cannot_list_users(api_user):
    client = make_client(api_user)
    res = client.get("/api/user/", format="json")
    assert res.status_code == 403


def test_staff_can_list_users(db, staff_user):
    client = make_client(staff_user)
    res = client.get("/api/user/", format="json")
    assert res.status_code == 200


def test_non_staff_cannot_list_validators(api_user):
    client = make_client(api_user)
    res = client.get("/api/validator/", format="json")
    assert res.status_code == 403


def test_staff_can_list_validators(db, staff_user, validator):
    client = make_client(staff_user)
    res = client.get("/api/validator/", format="json")
    assert res.status_code == 200


def test_non_staff_cannot_access_counter_refresh(api_user):
    client = make_client(api_user)
    res = client.get("/api/counter/refresh/", format="json")
    assert res.status_code == 403


def test_staff_can_access_counter_refresh(db, staff_user, counter, monkeypatch):
    monkeypatch.setattr("aurora.api.viewsets.counter.ScopedRateThrottle2.rate", "1000/day")
    client = make_client(staff_user)
    res = client.get("/api/counter/refresh/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_non_staff_cannot_list_flatpages(api_user):
    client = make_client(api_user)
    res = client.get("/api/flatpage/", format="json")
    assert res.status_code == 403


def test_non_staff_cannot_list_templates(api_user):
    client = make_client(api_user)
    res = client.get("/api/template/", format="json")
    assert res.status_code == 403


def test_non_staff_denied_sysinfo(api_user):
    client = make_client(api_user)
    res = client.get("/api/sys/", format="json")
    assert res.status_code in (401, 403)


def test_staff_allowed_sysinfo(db, staff_user):
    client = make_client(staff_user)
    res = client.get("/api/sys/", format="json")
    assert res.status_code == 200
    assert res.json()


# ---------------------------------------------------------------------------
# me endpoint is accessible to any authenticated user
# ---------------------------------------------------------------------------


def test_user_me_accessible_to_any_authenticated(api_user):
    client = make_client(api_user)
    res = client.get("/api/user/me/", format="json")
    assert res.status_code == 200
    assert res.json()
