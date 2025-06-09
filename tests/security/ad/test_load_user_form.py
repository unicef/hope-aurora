import pytest
from django.core.exceptions import ValidationError
from testutils.factories import GroupFactory, OrganizationFactory, ProjectFactory, RegistrationFactory

from aurora.security.ad import LoadUsersForm


@pytest.fixture
def group():
    return GroupFactory()


@pytest.fixture
def project():
    return ProjectFactory()


@pytest.fixture
def organization():
    return OrganizationFactory()


@pytest.fixture
def registration():
    return RegistrationFactory()


@pytest.mark.django_db
def test_clean_emails_valid_single_email(group, organization):
    form = LoadUsersForm(
        data={
            "emails": "user@example.com",
            "role": group.pk,
            "organization": organization.pk,
        }
    )

    form.cleaned_data = {"emails": "user@example.com"}

    result = form.clean_emails()
    assert result == "user@example.com"


@pytest.mark.django_db
def test_clean_emails_valid_multiple_emails(group, organization):
    form = LoadUsersForm(
        data={
            "emails": "user1@example.com user2@example.com user3@example.com",
            "role": group.pk,
            "organization": organization.pk,
        }
    )

    form.cleaned_data = {"emails": "user1@example.com user2@example.com user3@example.com"}

    result = form.clean_emails()
    assert result == "user1@example.com user2@example.com user3@example.com"


@pytest.mark.django_db
def test_clean_emails_invalid_single_email(group, organization):
    form = LoadUsersForm(
        data={
            "emails": "invalid-email",
            "role": group.pk,
            "organization": organization.pk,
        }
    )

    form.cleaned_data = {"emails": "invalid-email"}

    with pytest.raises(ValidationError) as exc_info:
        form.clean_emails()

    assert "Invalid emails invalid-email" in str(exc_info.value)


@pytest.mark.django_db
def test_clean_emails_mixed_valid_invalid_emails(group, organization):
    form = LoadUsersForm(
        data={
            "emails": "valid@example.com invalid-email user2@example.com",
            "role": group.pk,
            "organization": organization.pk,
        }
    )

    form.cleaned_data = {"emails": "valid@example.com invalid-email user2@example.com"}

    with pytest.raises(ValidationError) as exc_info:
        form.clean_emails()

    error_message = str(exc_info.value)
    assert "Invalid emails" in error_message
    assert "invalid-email" in error_message
    assert "valid@example.com" not in error_message
    assert "user2@example.com" not in error_message


@pytest.mark.django_db
def test_clean_emails_empty_string(group, organization):
    form = LoadUsersForm(
        data={
            "emails": "",
            "role": group.pk,
            "organization": organization.pk,
        }
    )

    form.cleaned_data = {"emails": ""}

    result = form.clean_emails()
    assert result == ""


@pytest.mark.django_db
def test_clean_valid_with_organization_only(group, organization):
    form = LoadUsersForm(
        data={
            "emails": "user@example.com",
            "role": group.pk,
            "organization": organization.pk,
        }
    )

    form.cleaned_data = {
        "emails": "user@example.com",
        "role": group,
        "organization": organization,
        "project": None,
        "registration": None,
    }

    form.clean()


@pytest.mark.django_db
def test_clean_valid_with_project_only(group):
    project = ProjectFactory()

    form = LoadUsersForm(
        data={
            "emails": "user@example.com",
            "role": group.pk,
            "project": project.pk,
        }
    )

    form.cleaned_data = {
        "emails": "user@example.com",
        "role": group,
        "organization": None,
        "project": project,
        "registration": None,
    }
    form.clean()


@pytest.mark.django_db
def test_clean_valid_with_registration_only(group, registration):
    form = LoadUsersForm(
        data={
            "emails": "user@example.com",
            "role": group.pk,
            "registration": registration.pk,
        }
    )

    form.cleaned_data = {
        "emails": "user@example.com",
        "role": group,
        "organization": None,
        "project": None,
        "registration": registration,
    }

    form.clean()


@pytest.mark.django_db
def test_clean_invalid_no_scope_set(group):
    form = LoadUsersForm(
        data={
            "emails": "user@example.com",
            "role": group.pk,
        }
    )

    form.cleaned_data = {
        "emails": "user@example.com",
        "role": group,
        "organization": None,
        "project": None,
        "registration": None,
    }

    with pytest.raises(ValidationError) as exc_info:
        form.clean()

    assert "You must set one scope" in str(exc_info.value)


@pytest.mark.django_db
def test_clean_invalid_multiple_scopes_set(group, organization, registration, project):
    form = LoadUsersForm(
        data={
            "emails": "user@example.com",
            "role": group.pk,
            "organization": organization.pk,
            "project": project.pk,
            "registration": registration.pk,
        }
    )

    form.cleaned_data = {
        "emails": "user@example.com",
        "role": group,
        "organization": organization,
        "project": project,
        "registration": registration,
    }

    with pytest.raises(ValidationError) as exc_info:
        form.clean()

    assert "You must set only one scope" in str(exc_info.value)
