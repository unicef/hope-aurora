import pytest

from aurora.core.models import Validator
from testutils.factories import FormFactory, RegistrationFactory


@pytest.mark.django_db
def test_validator_save_updates_flexform_version():
    validator = Validator.objects.create(
        label="test_validator", target=Validator.FORM, active=True, code="return true;"
    )

    flex_form = FormFactory(name="Test Form")
    flex_form.validator = validator
    flex_form.save()
    original_version = flex_form.version
    validator.save()
    flex_form.refresh_from_db()

    assert flex_form.version == original_version + 1
    assert flex_form.last_update_date is not None


@pytest.mark.django_db
def test_validator_save_updates_flexform_fields():
    validator = Validator.objects.create(
        label="field_validator", target=Validator.FIELD, active=True, code="return true;"
    )

    flex_form = FormFactory(name="Test Form")
    flex_form.fields.create(label="Test Field", field_type="django.forms.CharField", validator=validator)

    original_version = flex_form.version
    validator.save()
    flex_form.refresh_from_db()

    assert flex_form.version == original_version + 1


@pytest.mark.django_db
def test_validator_save_updates_registration():
    validator = Validator.objects.create(
        label="registration_validator", target=Validator.FORM, active=True, code="return true;"
    )

    registration = RegistrationFactory()
    registration.validator = validator
    registration.save()
    original_version = registration.version
    validator.save()
    registration.refresh_from_db()

    assert registration.version == original_version + 1


@pytest.mark.django_db
def test_validator_save_updates_registration_via_flexform():
    validator = Validator.objects.create(
        label="flexform_validator", target=Validator.FORM, active=True, code="return true;"
    )

    flex_form = FormFactory(name="Test Form")
    flex_form.validator = validator
    flex_form.save()

    registration = RegistrationFactory()
    registration.flex_form = flex_form
    registration.save()
    original_version = registration.version
    validator.save()
    registration.refresh_from_db()

    assert registration.version == original_version + 1


@pytest.mark.django_db
def test_flexformfield_save_catches_doesnotexist():
    from aurora.core.models import FlexFormField

    field = FlexFormField(
        label="Test Field",
        field_type="django.forms.CharField",
        flex_form_id=99999,  # Non-existent ID
    )

    field.save()
    assert field.pk is not None

    field.delete()
