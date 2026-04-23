import pytest
from django.contrib.auth.models import Group

from aurora.security.models import AuroraRole


@pytest.mark.django_db
def test_user_profile_str_and_custom_fields_persist():
    from testutils.factories import UserFactory

    user = UserFactory(username="profile-user")
    profile = user.profile
    profile.custom_fields = {"x": 1}
    profile.save()
    assert str(profile) == "profile-user"
    profile.refresh_from_db()
    assert profile.custom_fields == {"x": 1}


@pytest.mark.django_db
def test_aurora_role_save_sets_project_and_org_from_registration():
    from testutils.factories import RegistrationFactory
    from testutils.factories import UserFactory

    registration = RegistrationFactory()
    user = UserFactory(username="role-user-1")
    group = Group.objects.create(name="g-registration")

    role = AuroraRole(
        user=user,
        role=group,
        registration=registration,
    )
    role.save()
    assert role.project == registration.project
    assert role.organization == registration.project.organization


@pytest.mark.django_db
def test_aurora_role_save_sets_org_from_project():
    from testutils.factories import ProjectFactory
    from testutils.factories import UserFactory

    project = ProjectFactory()
    user = UserFactory(username="role-user-2")
    group = Group.objects.create(name="g-project")

    role = AuroraRole(
        user=user,
        role=group,
        project=project,
    )
    role.save()
    assert role.organization == project.organization


@pytest.mark.django_db
def test_aurora_role_natural_key_branches():
    from testutils.factories import OrganizationFactory
    from testutils.factories import ProjectFactory
    from testutils.factories import RegistrationFactory
    from testutils.factories import UserFactory

    user = UserFactory(username="role-user-3")
    group = Group.objects.create(name="g-key")
    organization = OrganizationFactory(slug="org-key")
    project = ProjectFactory(slug="prj-key")
    registration = RegistrationFactory(slug="reg-key")

    org_role = AuroraRole(user=user, role=group, organization=organization)
    assert org_role.natural_key() == ("org-key", None, None, "role-user-3", "g-key")

    project_role = AuroraRole(user=user, role=group, project=project)
    assert project_role.natural_key() == (None, "prj-key", None, "role-user-3", "g-key")

    reg_role = AuroraRole(user=user, role=group, registration=registration)
    assert reg_role.natural_key() == (None, None, "reg-key", "role-user-3", "g-key")

    plain_role = AuroraRole(user=user, role=group)
    assert plain_role.natural_key() == (None, None, None, "role-user-3", "g-key")


@pytest.mark.django_db
def test_role_manager_get_by_natural_key_scope_branches():
    from testutils.factories import AuroraRoleFactory
    from testutils.factories import ProjectFactory
    from testutils.factories import RegistrationFactory

    org_role = AuroraRoleFactory()
    found_org = AuroraRole.objects.get_by_natural_key(
        org_role.organization.slug,
        "",
        "",
        org_role.user.username,
        org_role.role.name,
    )
    assert found_org.pk == org_role.pk

    project = ProjectFactory(slug="prj-manager")
    prj_role = AuroraRoleFactory(organization=None, project=project)
    found_prj = AuroraRole.objects.get_by_natural_key(
        "",
        "prj-manager",
        "",
        prj_role.user.username,
        prj_role.role.name,
    )
    assert found_prj.pk == prj_role.pk

    registration = RegistrationFactory(slug="reg-manager")
    reg_role = AuroraRoleFactory(
        organization=None,
        project=None,
        registration=registration,
    )
    found_reg = AuroraRole.objects.get_by_natural_key(
        "",
        "",
        "reg-manager",
        reg_role.user.username,
        reg_role.role.name,
    )
    assert found_reg.pk == reg_role.pk

    found_plain = AuroraRole.objects.get_by_natural_key(
        "",
        "",
        "",
        reg_role.user.username,
        reg_role.role.name,
    )
    assert found_plain.pk == reg_role.pk
