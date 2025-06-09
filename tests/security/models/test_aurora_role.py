import pytest
from datetime import date

from aurora.security.models import AuroraRole
from testutils.factories import AuroraRoleFactory, GroupFactory, RegistrationFactory, ProjectFactory


@pytest.fixture
def project():
    return ProjectFactory()


@pytest.fixture
def simple_registration(project):
    return RegistrationFactory(name="Registration-#1", project=project)


@pytest.fixture
def group():
    return GroupFactory(name="test_role")


@pytest.mark.django_db
def test_get_by_natural_key_with_organization_slug(user, group, project):
    role = AuroraRoleFactory(user=user, role=group, organization=project.organization, project=None, registration=None)

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=project.organization.slug,
        prj_slug=None,
        registration_slug=None,
        username=user.username,
        group=group.name,
    )

    assert retrieved_role == role
    assert retrieved_role.organization == project.organization


@pytest.mark.django_db
def test_get_by_natural_key_with_project_slug(user, group, project):
    role = AuroraRoleFactory(user=user, role=group, organization=None, project=project, registration=None)

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=None,
        prj_slug=project.slug,
        registration_slug=None,
        username=user.username,
        group=group.name,
    )

    assert retrieved_role == role
    assert retrieved_role.project == project


@pytest.mark.django_db
def test_get_by_natural_key_with_registration_slug(user, group, simple_registration):
    role = AuroraRoleFactory(user=user, role=group, organization=None, project=None, registration=simple_registration)

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=None,
        prj_slug=None,
        registration_slug=simple_registration.slug,
        username=user.username,
        group=group.name,
    )

    assert retrieved_role == role
    assert retrieved_role.registration == simple_registration


@pytest.mark.django_db
def test_get_by_natural_key_no_filter(user, group):
    role = AuroraRoleFactory(user=user, role=group, organization=None, project=None, registration=None)

    retrieved_role = AuroraRole.objects.get_by_natural_key(
        org_slug=None, prj_slug=None, registration_slug=None, username=user.username, group=group.name
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
def test_get_by_natural_key_multiple_objects_returned(user, group, project):
    AuroraRole.objects.create(user=user, role=group, organization=project.organization, valid_from=date(2023, 1, 1))

    AuroraRole.objects.create(user=user, role=group, organization=project.organization, valid_from=date(2024, 1, 1))
    with pytest.raises(AuroraRole.MultipleObjectsReturned):
        AuroraRole.objects.get_by_natural_key(
            org_slug=project.organization.slug,
            prj_slug=None,
            registration_slug=None,
            username=user.username,
            group=group.name,
        )


@pytest.mark.django_db
def test_natural_key_with_organization(user, group, project):
    role = AuroraRoleFactory(user=user, role=group, organization=project.organization, project=None, registration=None)

    natural_key = role.natural_key()

    assert natural_key == (
        project.organization.slug,
        None,
        None,
        user.username,
        group.name,
    )


@pytest.mark.django_db
@pytest.mark.xfail
def test_natural_key_with_project(user, group, project):
    role = AuroraRoleFactory(user=user, role=group, organization=None, project=project, registration=None)

    natural_key = role.natural_key()

    assert natural_key == (None, project.slug, None, user.username, group.name)


@pytest.mark.django_db
@pytest.mark.xfail
def test_natural_key_with_registration(user, group, simple_registration):
    role = AuroraRoleFactory(user=user, role=group, organization=None, project=None, registration=simple_registration)

    natural_key = role.natural_key()

    assert natural_key == (None, None, simple_registration.slug, user.username, group.name)


@pytest.mark.django_db
def test_natural_key_no_context(user, group):
    role = AuroraRoleFactory(user=user, role=group, organization=None, project=None, registration=None)

    natural_key = role.natural_key()

    assert natural_key == (None, None, None, user.username, group.name)
