"""The API must answer "whose records?", not only "may this user read records?"."""

from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework.test import APIClient
from testutils.factories import (
    CounterFactory,
    FlexFormFieldFactory,
    FormFactory,
    FormSetFactory,
    OrganizationFactory,
    ProjectFactory,
    RecordFactory,
    RegistrationFactory,
    SuperUserFactory,
    UserFactory,
    ValidatorFactory,
)
from testutils.perms import get_group, user_grant_permissions


def _tenant(name: str) -> SimpleNamespace:
    organization = OrganizationFactory(name=f"{name} Organization")
    project = ProjectFactory(name=f"{name} Project", organization=organization)
    registration = RegistrationFactory(name=f"{name} Registration", project=project)
    return SimpleNamespace(
        organization=organization,
        project=project,
        registration=registration,
        record=RecordFactory(registration=registration),
    )


@pytest.fixture
def ours(db) -> SimpleNamespace:
    return _tenant("Ours")


@pytest.fixture
def theirs(db) -> SimpleNamespace:
    """A hierarchy the user under test has no role in, so that a leak shows up as an extra row."""
    return _tenant("Theirs")


@pytest.fixture
def user(db):
    return UserFactory()


@pytest.fixture
def client(user) -> APIClient:
    client = APIClient()
    client.force_authenticate(user)
    return client


def ids(response) -> set[str]:
    payload = response.json()
    rows = payload["results"] if isinstance(payload, dict) else payload
    return {str(row.get("id") or row.get("pk")) for row in rows}


def test_records_of_other_organizations_are_not_listed(ours, theirs, user, client):
    with user_grant_permissions(user, ["registration.view_record"], ours.organization):
        response = client.get("/api/record/", format="json")
    assert response.status_code == 200
    assert ids(response) == {str(ours.record.pk)}


def test_record_of_another_organization_is_not_retrievable(ours, theirs, user, client):
    with user_grant_permissions(user, ["registration.view_record"], ours.organization):
        assert client.get(f"/api/record/{ours.record.pk}/", format="json").status_code == 200
        assert client.get(f"/api/record/{theirs.record.pk}/", format="json").status_code == 404


def test_record_metadata_describes_the_requested_record(ours, theirs, user, client):
    """It used to report Record.objects.latest(), exposing the newest row in any organization."""
    with user_grant_permissions(user, ["registration.view_record"], ours.organization):
        response = client.get(f"/api/record/{ours.record.pk}/metadata/", format="json")
        assert client.get(f"/api/record/{theirs.record.pk}/metadata/", format="json").status_code == 404
    body = response.json()
    assert body["id"] == ours.record.pk
    assert body["registration"] == ours.record.registration_id
    assert parse_datetime(body["timestamp"]) == ours.record.timestamp


def test_registrations_of_other_organizations_are_not_listed(ours, theirs, user, client):
    with user_grant_permissions(user, ["registration.view_registration"], ours.organization):
        response = client.get("/api/registration/", format="json")
    assert ids(response) == {str(ours.registration.pk)}


def test_projects_of_other_organizations_are_not_listed(ours, theirs, user, client):
    with user_grant_permissions(user, ["core.view_project"], ours.organization):
        response = client.get("/api/project/", format="json")
    assert ids(response) == {str(ours.project.pk)}


def test_other_organizations_are_not_listed(ours, theirs, user, client):
    with user_grant_permissions(user, ["core.view_organization"], ours.organization):
        response = client.get("/api/organization/", format="json")
    assert ids(response) == {str(ours.organization.pk)}


def test_capability_without_a_role_grants_no_data(ours, theirs, user, client):
    """A permission on its own says what a user may read, never whose."""
    with user_grant_permissions(user, ["registration.view_record"]):
        response = client.get("/api/record/", format="json")
    assert response.status_code == 200
    assert ids(response) == set()


def test_an_unscoped_role_is_a_deliberate_grant_over_everything(ours, theirs, user, client):
    """Roles carrying no organization, project or registration are how global access is provisioned."""
    group = user_grant_permissions(user, ["registration.view_record"])
    with group:
        from aurora.security.models import AuroraRole

        AuroraRole.objects.create(user=user, role=group.group)
        response = client.get("/api/record/", format="json")
    assert ids(response) == {str(ours.record.pk), str(theirs.record.pk)}


class TestRegistrationScopedRole:
    """A role on a single registration must not open up its siblings."""

    @pytest.fixture
    def sibling(self, ours) -> SimpleNamespace:
        registration = RegistrationFactory(name="Sibling Registration", project=ours.project)
        return SimpleNamespace(registration=registration, record=RecordFactory(registration=registration))

    def test_sibling_registrations_are_not_listed(self, ours, sibling, user, client):
        with user_grant_permissions(user, ["registration.view_registration"], ours.registration):
            response = client.get("/api/registration/", format="json")
        assert ids(response) == {str(ours.registration.pk)}

    def test_sibling_records_are_not_listed(self, ours, sibling, user, client):
        with user_grant_permissions(user, ["registration.view_record"], ours.registration):
            response = client.get("/api/record/", format="json")
        assert ids(response) == {str(ours.record.pk)}

    def test_the_containing_project_stays_visible(self, ours, theirs, user, client):
        """Without upward visibility the hierarchy cannot be navigated from a registration role."""
        with user_grant_permissions(user, ["core.view_project"], ours.registration):
            response = client.get("/api/project/", format="json")
        assert ids(response) == {str(ours.project.pk)}

    def test_the_containing_organization_stays_visible(self, ours, theirs, user, client):
        with user_grant_permissions(user, ["core.view_organization"], ours.registration):
            response = client.get("/api/organization/", format="json")
        assert ids(response) == {str(ours.organization.pk)}


class TestNestedRoutes:
    """These build their querysets by hand, so they bypass the filter backends unless told otherwise."""

    def test_projects_of_an_organization_are_scoped(self, ours, theirs, user, client):
        with user_grant_permissions(user, ["core.view_organization", "core.view_project"], ours.project):
            response = client.get(f"/api/organization/{ours.organization.pk}/projects/", format="json")
            assert ids(response) == {str(ours.project.pk)}
            foreign = client.get(f"/api/organization/{theirs.organization.pk}/projects/", format="json")
        assert foreign.status_code == 404

    def test_registrations_of_a_project_are_scoped(self, ours, theirs, user, client):
        with user_grant_permissions(user, ["core.view_project", "registration.view_registration"], ours.registration):
            response = client.get(f"/api/project/{ours.project.pk}/registrations/", format="json")
            assert ids(response) == {str(ours.registration.pk)}
            foreign = client.get(f"/api/project/{theirs.project.pk}/registrations/", format="json")
        assert foreign.status_code == 404

    def test_sibling_registrations_are_hidden_on_the_project_route(self, ours, user, client):
        sibling = RegistrationFactory(name="Sibling Registration", project=ours.project)
        with user_grant_permissions(user, ["core.view_project", "registration.view_registration"], ours.registration):
            response = client.get(f"/api/project/{ours.project.pk}/registrations/", format="json")
        assert ids(response) == {str(ours.registration.pk)}
        assert str(sibling.pk) not in ids(response)

    def test_sibling_projects_are_hidden_on_the_organization_route(self, ours, user, client):
        sibling = ProjectFactory(name="Sibling Project", organization=ours.organization)
        with user_grant_permissions(user, ["core.view_organization", "core.view_project"], ours.project):
            response = client.get(f"/api/organization/{ours.organization.pk}/projects/", format="json")
        assert ids(response) == {str(ours.project.pk)}
        assert str(sibling.pk) not in ids(response)


class TestUserDirectory:
    def test_users_outside_the_hierarchy_are_not_listed(self, ours, theirs, user, client):
        outsider = UserFactory(username="outsider")
        with user_grant_permissions(outsider, ["security.view_user"], theirs.organization):
            pass
        colleague = UserFactory(username="colleague")
        with user_grant_permissions(colleague, ["security.view_user"], ours.organization):
            with user_grant_permissions(user, ["security.view_user"], ours.organization):
                response = client.get("/api/user/", format="json")
            listed = ids(response)
        assert str(colleague.pk) in listed
        assert str(outsider.pk) not in listed

    def test_the_caller_can_always_see_themselves(self, ours, user, client):
        with user_grant_permissions(user, ["security.view_user"]):
            response = client.get("/api/user/", format="json")
            own = client.get(f"/api/user/{user.pk}/", format="json")
        assert ids(response) == {str(user.pk)}
        assert own.status_code == 200
        assert own.json()["pk"] == user.pk

    def test_a_colleague_is_retrievable_and_an_outsider_is_not(self, ours, theirs, user, client):
        outsider = UserFactory(username="outsider")
        with user_grant_permissions(outsider, ["security.view_user"], theirs.organization):
            pass
        colleague = UserFactory(username="colleague")
        with user_grant_permissions(colleague, ["security.view_user"], ours.organization):
            with user_grant_permissions(user, ["security.view_user"], ours.organization):
                own = client.get(f"/api/user/{colleague.pk}/", format="json")
                foreign = client.get(f"/api/user/{outsider.pk}/", format="json")
        assert own.status_code == 200
        assert own.json()["pk"] == colleague.pk
        assert foreign.status_code == 404

    def test_a_superuser_lists_users_outside_any_shared_hierarchy(self, ours, theirs, client):
        insider = UserFactory(username="insider")
        outsider = UserFactory(username="far-outsider")
        client.force_authenticate(SuperUserFactory())
        response = client.get("/api/user/", format="json")
        listed = ids(response)
        assert str(insider.pk) in listed
        assert str(outsider.pk) in listed


def test_shared_reference_data_stays_readable(db, user, client):
    """Validators, option sets and templates belong to no organization and carry no personal data."""
    validator = ValidatorFactory()
    with user_grant_permissions(user, ["core.view_validator"]):
        response = client.get("/api/validator/", format="json")
    assert response.status_code == 200
    assert str(validator.pk) in ids(response)


def test_registration_metadata_stays_public(ours, user, client):
    """Applicants load a registration's definition before they have any role."""
    anonymous = APIClient()
    assert anonymous.get(f"/api/registration/{ours.registration.pk}/metadata/", format="json").status_code == 200
    with user_grant_permissions(user, ["registration.view_registration"], ours.organization):
        response = client.get(f"/api/registration/{ours.registration.pk}/metadata/", format="json")
    assert response.status_code == 200


def test_registration_metadata_is_public_even_outside_the_callers_scope(ours, theirs, user, client):
    with user_grant_permissions(user, ["registration.view_registration"], theirs.organization):
        response = client.get(f"/api/registration/{ours.registration.pk}/metadata/", format="json")
    assert response.status_code == 200


class TestScopedModels:
    """Forms, fields, form sets and counters sit on the same hierarchy as the records they describe."""

    def test_forms_of_other_projects_are_not_listed(self, ours, theirs, user, client):
        own = FormFactory(name="Ours Form", project=ours.project)
        hidden = FormFactory(name="Theirs Form", project=theirs.project)
        with user_grant_permissions(user, ["core.view_flexform"], ours.project):
            response = client.get("/api/form/", format="json")
            foreign = client.get(f"/api/form/{hidden.pk}/", format="json")
        assert ids(response) == {str(own.pk)}
        assert foreign.status_code == 404

    def test_fields_follow_their_form(self, ours, theirs, user, client):
        own = FlexFormFieldFactory(flex_form=FormFactory(name="Ours Field Form", project=ours.project))
        foreign_field = FlexFormFieldFactory(flex_form=FormFactory(name="Theirs Field Form", project=theirs.project))
        with user_grant_permissions(user, ["core.view_flexformfield"], ours.project):
            response = client.get("/api/field/", format="json")
            foreign = client.get(f"/api/field/{foreign_field.pk}/", format="json")
        assert ids(response) == {str(own.pk)}
        assert foreign.status_code == 404

    def test_formsets_follow_their_parent_form(self, ours, theirs, user, client):
        own_form = FormFactory(name="Ours Parent", project=ours.project)
        theirs_form = FormFactory(name="Theirs Parent", project=theirs.project)
        own = FormSetFactory(name="Ours Set", parent=own_form, flex_form=own_form)
        FormSetFactory(name="Theirs Set", parent=theirs_form, flex_form=theirs_form)
        with user_grant_permissions(user, ["core.view_formset"], ours.project):
            response = client.get("/api/formset/", format="json")
        assert ids(response) == {str(own.pk)}

    def test_counters_follow_their_registration(self, ours, theirs, user, client):
        own = CounterFactory(registration=ours.registration)
        foreign_counter = CounterFactory(registration=theirs.registration)
        with user_grant_permissions(user, ["counters.view_counter"], ours.registration):
            listed = client.get("/api/counter/", format="json")
            own_detail = client.get(f"/api/counter/{own.pk}/", format="json")
            foreign = client.get(f"/api/counter/{foreign_counter.pk}/", format="json")
        assert listed.status_code == 200
        assert len(listed.json()["results"]) == 1
        assert own_detail.status_code == 200
        assert foreign.status_code == 404


class TestRoleWindow:
    def test_an_expired_role_grants_no_data(self, ours, theirs, user, client):
        with user_grant_permissions(user, ["registration.view_record"], ours.organization):
            from aurora.security.models import AuroraRole

            AuroraRole.objects.filter(user=user).update(valid_until=timezone.localdate() - timedelta(days=1))
            response = client.get("/api/record/", format="json")
        assert response.status_code == 200
        assert ids(response) == set()

    def test_a_role_that_has_not_started_grants_no_data(self, ours, user, client):
        with user_grant_permissions(user, ["registration.view_record"], ours.organization):
            from aurora.security.models import AuroraRole

            AuroraRole.objects.filter(user=user).update(valid_from=timezone.localdate() + timedelta(days=1))
            response = client.get("/api/record/", format="json")
        assert ids(response) == set()

    def test_a_registration_only_role_created_in_bulk_still_scopes(self, ours, theirs, user, client):
        """bulk_create skips AuroraRole.save(), leaving organization and project empty."""
        from aurora.security.models import AuroraRole

        group = get_group(permissions=["registration.view_record"])
        user.groups.add(group)
        AuroraRole.objects.bulk_create([AuroraRole(user=user, role=group, registration=ours.registration)])
        stored = AuroraRole.objects.get(user=user, role=group)
        assert stored.organization_id is None
        assert stored.project_id is None

        response = client.get("/api/record/", format="json")
        assert ids(response) == {str(ours.record.pk)}


def test_a_superuser_sees_every_organization(ours, theirs, client):
    client.force_authenticate(SuperUserFactory())
    response = client.get("/api/record/", format="json")
    assert ids(response) == {str(ours.record.pk), str(theirs.record.pk)}
