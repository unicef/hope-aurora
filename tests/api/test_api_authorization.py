"""Authorization tests for the DRF API.

Regression tests for broken access control (CWE-284): an authenticated user
must only be able to enumerate and interact with resources inside the
organization/project/registration scope covered by their active role
assignments. Superusers (root) retain full access.
"""

from typing import TYPE_CHECKING

import pytest
from django.contrib.auth.models import Permission
from rest_framework.test import APIClient
from testutils.factories import (
    AuroraRoleFactory,
    GroupFactory,
    RecordFactory,
    TokenProxyFactory,
    UserFactory,
)

if TYPE_CHECKING:
    from django.contrib.auth import get_user_model

    User = get_user_model()

    from aurora.core.models import FlexForm, Organization, Project
    from aurora.registration.models import Registration


@pytest.fixture
def org_a(db) -> "Organization":
    from testutils.factories import OrganizationFactory

    return OrganizationFactory(name="Org A")


@pytest.fixture
def org_b(db) -> "Organization":
    from testutils.factories import OrganizationFactory

    return OrganizationFactory(name="Org B")


@pytest.fixture
def project_a(org_a) -> "Project":
    from testutils.factories import ProjectFactory

    return ProjectFactory(name="Project A", organization=org_a)


@pytest.fixture
def project_b(org_b) -> "Project":
    from testutils.factories import ProjectFactory

    return ProjectFactory(name="Project B", organization=org_b)


@pytest.fixture
def form_a(project_a) -> "FlexForm":
    from testutils.factories import FormFactory

    return FormFactory(name="Form A", project=project_a)


@pytest.fixture
def form_b(project_b) -> "FlexForm":
    from testutils.factories import FormFactory

    return FormFactory(name="Form B", project=project_b)


@pytest.fixture
def registration_a(project_a, form_a) -> "Registration":
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(name="Registration A", project=project_a, flex_form=form_a)


@pytest.fixture
def registration_b(project_b, form_b) -> "Registration":
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(name="Registration B", project=project_b, flex_form=form_b)


@pytest.fixture
def record_a(registration_a):
    return RecordFactory(registration=registration_a)


@pytest.fixture
def record_b(registration_b):
    return RecordFactory(registration=registration_b)


@pytest.fixture
def scoped_user(db) -> "User":
    return UserFactory(username="scoped", is_staff=False, is_superuser=False)


@pytest.fixture
def unprivileged_user(db) -> "User":
    return UserFactory(username="unprivileged", is_staff=False, is_superuser=False)


@pytest.fixture
def form_viewer_role(scoped_user, registration_a):
    """A 'Form Viewer' role scoped to registration A with can_view_data permission."""
    group = GroupFactory(name="Form Viewer")
    can_view_data = Permission.objects.get(codename="can_view_data", content_type__app_label="registration")
    group.permissions.add(can_view_data)
    return AuroraRoleFactory(registration=registration_a, user=scoped_user, role=group)


def _token_client(user):
    client = APIClient()
    token = TokenProxyFactory(user=user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


@pytest.fixture
def admin_client(admin_user):
    return _token_client(admin_user)


@pytest.fixture
def scoped_client(scoped_user, form_viewer_role):
    return _token_client(scoped_user)


@pytest.fixture
def unprivileged_client(unprivileged_user):
    return _token_client(unprivileged_user)


def test_unprivileged_user_is_denied(
    unprivileged_client,
    org_a,
    project_a,
    registration_a,
    record_a,
    form_a,
):
    """An authenticated user without any role assignment cannot access the API."""
    assert unprivileged_client.get("/api/organization/").status_code == 403
    assert unprivileged_client.get(f"/api/organization/{org_a.pk}/").status_code == 403
    assert unprivileged_client.get("/api/project/").status_code == 403
    assert unprivileged_client.get(f"/api/project/{project_a.pk}/").status_code == 403
    assert unprivileged_client.get("/api/registration/").status_code == 403
    assert unprivileged_client.get("/api/record/").status_code == 403
    assert unprivileged_client.get("/api/form/").status_code == 403
    assert unprivileged_client.get("/api/user/").status_code == 403


def test_scoped_user_cannot_enumerate_out_of_scope_organization(
    scoped_client,
    org_a,
    org_b,
):
    res = scoped_client.get("/api/organization/", format="json")
    assert res.status_code == 200
    assert {row["id"] for row in res.json()["results"]} == {org_a.pk}
    assert scoped_client.get(f"/api/organization/{org_b.pk}/").status_code == 404
    assert scoped_client.get(f"/api/organization/{org_a.pk}/").status_code == 200


def test_scoped_user_cannot_enumerate_out_of_scope_project(
    scoped_client,
    org_a,
    project_a,
    project_b,
):
    res = scoped_client.get("/api/project/", format="json")
    assert res.status_code == 200
    assert {row["id"] for row in res.json()["results"]} == {project_a.pk}
    assert scoped_client.get(f"/api/project/{project_b.pk}/").status_code == 404


def test_scoped_user_cannot_enumerate_out_of_scope_registration(
    scoped_client,
    org_a,
    registration_a,
    registration_b,
):
    res = scoped_client.get("/api/registration/", format="json")
    assert res.status_code == 200
    assert {row["id"] for row in res.json()["results"]} == {registration_a.pk}
    assert scoped_client.get(f"/api/registration/{registration_b.pk}/").status_code == 404


def test_scoped_user_cannot_read_out_of_scope_record(
    scoped_client,
    org_a,
    record_a,
    record_b,
):
    res = scoped_client.get("/api/record/", format="json")
    assert res.status_code == 200
    assert {row["id"] for row in res.json()["results"]} == {record_a.pk}
    assert scoped_client.get(f"/api/record/{record_b.pk}/").status_code == 404


def test_scoped_user_cannot_enumerate_out_of_scope_form(
    scoped_client,
    org_a,
    form_a,
    form_b,
):
    res = scoped_client.get("/api/form/", format="json")
    assert res.status_code == 200
    assert {row["id"] for row in res.json()["results"]} == {form_a.pk}
    assert scoped_client.get(f"/api/form/{form_b.pk}/").status_code == 404


def test_scoped_user_can_read_records_in_scope(
    scoped_client,
    org_a,
    registration_a,
    record_a,
):
    """The Form Viewer role has can_view_data, so records in scope are readable."""
    res = scoped_client.get(f"/api/registration/{registration_a.pk}/records/", format="json")
    assert res.status_code == 200
    ids = {row["pk"] for row in res.json()["results"]}
    assert record_a.pk in ids


def test_scoped_user_without_export_permission_cannot_export(
    scoped_client,
    org_a,
    registration_a,
):
    """CSV export requires the registration.export_data permission."""
    res = scoped_client.get(f"/api/registration/{registration_a.pk}/csv/")
    assert res.status_code == 403


def test_scoped_user_cannot_access_out_of_scope_records_action(
    scoped_client,
    org_a,
    registration_b,
):
    res = scoped_client.get(f"/api/registration/{registration_b.pk}/records/")
    assert res.status_code == 404


def test_scoped_user_cannot_list_users(
    scoped_client,
    scoped_user,
    unprivileged_user,
    record_a,
):
    """User enumeration is restricted to superusers."""
    res = scoped_client.get("/api/user/", format="json")
    assert res.status_code == 200
    assert res.json()["count"] == 0

    assert scoped_client.get(f"/api/user/{unprivileged_user.pk}/").status_code == 404
    assert scoped_client.get("/api/user/me/").status_code == 200


def test_registration_scoped_role_covers_upward_scope(
    scoped_user,
    registration_a,
    project_a,
    org_a,
    record_a,
):
    """A registration-scoped role grants access to the registration, its project, and its org."""
    AuroraRoleFactory(registration=registration_a, user=scoped_user, role=GroupFactory(name="Form Viewer"))
    assert registration_a.pk in scoped_user.accessible_registration_ids
    assert project_a.pk in scoped_user.accessible_project_ids
    assert org_a.pk in scoped_user.accessible_organization_ids


def test_org_scoped_role_does_not_cascade_downward(
    scoped_user,
    org_a,
    project_a,
    registration_a,
):
    """An org-scoped role grants the org only; it does not cascade to projects/registrations."""
    AuroraRoleFactory(organization=org_a, user=scoped_user, role=GroupFactory(name="Form Viewer"))
    assert org_a.pk in scoped_user.accessible_organization_ids
    assert project_a.pk not in scoped_user.accessible_project_ids
    assert registration_a.pk not in scoped_user.accessible_registration_ids


def test_superuser_sees_everything(
    scoped_user,
    admin_client,
    org_a,
    org_b,
    project_a,
    project_b,
    registration_a,
    registration_b,
    record_a,
    record_b,
    form_a,
    form_b,
):
    assert admin_client.get("/api/organization/").status_code == 200
    assert admin_client.get(f"/api/organization/{org_b.pk}/").status_code == 200
    assert admin_client.get(f"/api/project/{project_b.pk}/").status_code == 200
    assert admin_client.get(f"/api/registration/{registration_b.pk}/").status_code == 200
    assert admin_client.get(f"/api/record/{record_b.pk}/").status_code == 200
    assert admin_client.get(f"/api/form/{form_b.pk}/").status_code == 200

    res = admin_client.get("/api/organization/", format="json")
    assert {row["id"] for row in res.json()["results"]} == {org_a.pk, org_b.pk}


def test_public_registration_version_remains_accessible(
    django_app,
    registration_a,
):
    """The public version endpoint must stay reachable without authentication."""
    res = django_app.get(f"/api/registration/{registration_a.pk}/version/")
    assert res.status_code == 200
    assert res.json["version"] == registration_a.version
