import pytest
from datetime import date

from aurora.security.models import AuroraRole
from testutils.factories import (
    AuroraRoleFactory,
    GroupFactory,
    RegistrationFactory,
)


@pytest.fixture
def simple_registration(simple_form):
    return RegistrationFactory(name="Registration-#1", project=simple_form.project)


@pytest.fixture
def test_group():
    return GroupFactory(name="test_role")


@pytest.mark.django_db
def test_get_by_natural_key_with_organization_slug(user, test_group, simple_form):
    role = AuroraRoleFactory(
        user=user, role=test_group, organization=simple_form.project.organization, project=None, registration=None
    )

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=simple_form.project.organization.slug,
        prj_slug=None,
        registration_slug=None,
        username=user.username,
        group=test_group.name,
    )

    assert retrieved_role == role
    assert retrieved_role.organization == simple_form.project.organization


@pytest.mark.django_db
def test_get_by_natural_key_with_project_slug(user, test_group, simple_form):
    role = AuroraRoleFactory(
        user=user, role=test_group, organization=None, project=simple_form.project, registration=None
    )

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=None,
        prj_slug=simple_form.project.slug,
        registration_slug=None,
        username=user.username,
        group=test_group.name,
    )

    assert retrieved_role == role
    assert retrieved_role.project == simple_form.project


@pytest.mark.django_db
def test_get_by_natural_key_with_registration_slug(user, test_group, simple_registration):
    role = AuroraRoleFactory(
        user=user, role=test_group, organization=None, project=None, registration=simple_registration
    )

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=None,
        prj_slug=None,
        registration_slug=simple_registration.slug,
        username=user.username,
        group=test_group.name,
    )

    assert retrieved_role == role
    assert retrieved_role.registration == simple_registration


@pytest.mark.django_db
def test_get_by_natural_key_no_filter(user, test_group):
    role = AuroraRoleFactory(user=user, role=test_group, organization=None, project=None, registration=None)

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=None, prj_slug=None, registration_slug=None, username=user.username, group=test_group.name
    )

    assert retrieved_role == role
    assert retrieved_role.organization is None
    assert retrieved_role.project is None
    assert retrieved_role.registration is None


@pytest.mark.django_db
def test_get_by_natural_key_does_not_exist():
    with pytest.raises(AuroraRole.DoesNotExist):
        AuroraRole.objects.get_by_natural_key(
            org_slug="nonexistent-org",
            prj_slug=None,
            registration_slug=None,
            username="nonexistent",
            group="nonexistent_role",
        )


@pytest.mark.django_db
def test_get_by_natural_key_multiple_objects_returned(user, test_group, simple_form):
    AuroraRole.objects.create(
        user=user, role=test_group, organization=simple_form.project.organization, valid_from=date(2023, 1, 1)
    )

    AuroraRole.objects.create(
        user=user, role=test_group, organization=simple_form.project.organization, valid_from=date(2024, 1, 1)
    )
    with pytest.raises(AuroraRole.MultipleObjectsReturned):
        AuroraRole.objects.get_by_natural_key(
            org_slug=simple_form.project.organization.slug,
            prj_slug=None,
            registration_slug=None,
            username=user.username,
            group=test_group.name,
        )
