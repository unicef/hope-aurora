import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from typing import Any

from aurora.core.models import FlexForm, FormSet
from aurora.registration.models import Record


@pytest.mark.django_db
def test_create_form(db: Any) -> None:
    from testutils.factories import FormFactory

    form = FormFactory(name="test")
    assert form


@pytest.mark.django_db
def test_fixed_formset(db: Any) -> None:
    from testutils.factories import FormFactory

    master = FormFactory(name="Master")
    detail = FormFactory(name="Detail")
    fs = master.add_formset(detail, extra=1, dynamic=False)
    assert fs.name == "details"


@pytest.mark.django_db
def test_add_formset(db: Any) -> None:
    from testutils.factories import FormFactory

    master = FormFactory(name="Master")
    detail = FormFactory(name="Detail")
    fs: FormSet = master.add_formset(detail)
    assert fs.name == "details"


@pytest.mark.django_db
def test_simple_form(simple_form: "FlexForm") -> None:
    assert simple_form.name == "Form1"
    assert simple_form.fields.count() == 7
    assert simple_form.fields.filter(label="First Name").exists()
    assert simple_form.fields.filter(label="Last Name", validator__label="length_2_10").exists()
    assert simple_form.fields.filter(label="Image", field_type="django.forms.fields.ImageField").exists()


@pytest.mark.django_db
def test_complex_form(complex_form: "FlexForm") -> None:
    assert complex_form.name == "Form2"
    assert complex_form.fields.count() == 6
    assert complex_form.fields.filter(label="Family Name").exists()

    formset = complex_form.formsets.first()
    assert formset.name == "formset-0"

    nested_form = formset.flex_form
    assert nested_form.name == "Form2"
    assert nested_form.fields.count() == 6
    assert nested_form.fields.filter(label="First Name").exists()
    assert nested_form.fields.filter(label="Last Name").exists()
    assert nested_form.fields.filter(label="Date Of Birth").exists()
    assert nested_form.fields.filter(label="Image").exists()
    assert nested_form.fields.filter(label="File").exists()


@pytest.mark.django_db
def test_simple__valid_data(simple_form: "FlexForm", mock_storage: None) -> None:
    from testutils.factories import RegistrationFactory

    registration = RegistrationFactory(flex_form=simple_form)
    form_class = simple_form.get_form_class()
    with open("tests/data/image.png", "rb") as f:
        form = form_class(
            data={
                "first_name": "John",
                "last_name": "Doe",
                "index_no": "123",
            },
            files={
                "Image": SimpleUploadedFile("image.png", f.read()),
                "File": SimpleUploadedFile("file.txt", b"content"),
            },
        )
    assert form.is_valid(), form.errors
    instance: Record = registration.add_record(form.cleaned_data)
    assert instance


@pytest.mark.django_db
def test_simple__invalid_data(simple_form: "FlexForm", mock_storage: None) -> None:
    form_class = simple_form.get_form_class()
    with open("tests/data/image.png", "rb") as f:
        form = form_class(
            data={
                "first_name": "John",
                "last_name": "D",
                "index_no": "123",
            },
            files={
                "Image": SimpleUploadedFile("image.png", f.read()),
                "File": SimpleUploadedFile("file.txt", b"content"),
            },
        )
    assert not form.is_valid()
    assert "last_name" in form.errors


@pytest.mark.django_db
def test_complex__valid_data(complex_form: "FlexForm", mock_storage: None) -> None:
    from testutils.factories import RegistrationFactory

    registration = RegistrationFactory(flex_form=complex_form)
    form_class = complex_form.get_form_class()
    with open("tests/data/image.png", "rb") as f:
        form = form_class(
            data={
                "family_name": "Smith",
                "formset-0-TOTAL_FORMS": 1,
                "formset-0-INITIAL_FORMS": 0,
                "formset-0-MIN_NUM_FORMS": 0,
                "formset-0-MAX_NUM_FORMS": 1000,
                "formset-0-0-first_name": "Jane",
                "formset-0-0-last_name": "Smith",
                "formset-0-0-date_of_birth": "1990-01-01",
            },
            files={
                "formset-0-0-Image": SimpleUploadedFile("image.png", f.read()),
                "formset-0-0-File": SimpleUploadedFile("file.txt", b"content"),
            },
        )
    assert form.is_valid(), form.errors
    instance: Record = registration.add_record(form.cleaned_data)
    assert instance


@pytest.mark.django_db
def test_complex__invalid_data(complex_form: "FlexForm", mock_storage: None) -> None:
    form_class = complex_form.get_form_class()

    with open("tests/data/image.png", "rb") as f:
        form = form_class(
            data={
                "family_name": "Smith",
                "formset-0-TOTAL_FORMS": 1,
                "formset-0-INITIAL_FORMS": 0,
                "formset-0-MIN_NUM_FORMS": 0,
                "formset-0-MAX_NUM_FORMS": 1000,
                "formset-0-0-first_name": "Jane",
                "formset-0-0-last_name": "S",  # This should cause an error
                "formset-0-0-date_of_birth": "1990-01-01",
            },
            files={
                "formset-0-0-Image": SimpleUploadedFile("image.png", f.read()),
                "formset-0-0-File": SimpleUploadedFile("file.txt", b"content"),
            },
        )

        assert form.is_valid(), form.errors

    with open("tests/data/image.png", "rb") as f:
        form = form_class(
            data={
                "formset-0-TOTAL_FORMS": 1,
                "formset-0-INITIAL_FORMS": 0,
                "formset-0-MIN_NUM_FORMS": 0,
                "formset-0-MAX_NUM_FORMS": 1000,
                "formset-0-0-first_name": "Jane",
                "formset-0-0-last_name": "Smith",
                "formset-0-0-date_of_birth": "1990-01-01",
            },
            files={
                "formset-0-0-Image": SimpleUploadedFile("image.png", f.read()),
                "formset-0-0-File": SimpleUploadedFile("file.txt", b"content"),
            },
        )

    assert not form.is_valid()
    assert "family_name" in form.errors


@pytest.mark.django_db
def test_registration_with_simple_form(simple_form: "FlexForm", simple_registration: "FlexForm") -> None:
    """Test a registration with a simple form as the flex_form."""
    rg = simple_registration
    assert rg.flex_form == simple_form
    assert rg.flex_form.name == "Form1"
    assert rg.flex_form.fields.count() == 7
    assert rg.flex_form.fields.filter(label="Name").exists()


@pytest.mark.django_db
def test_registration_with_complex_form(complex_form: "FlexForm", complex_registration: "FlexForm") -> None:
    """Test a registration with a complex form as the flex_form."""
    rg = complex_registration
    assert rg.flex_form == complex_form
    assert rg.flex_form.name == "Form2"
    assert rg.flex_form.fields.count() == 6
    assert rg.flex_form.fields.filter(label="Family Name").exists()

    formset = rg.flex_form.formsets.first()
    assert formset.name == "formset-0"
    assert formset.flex_form.name == "Form2"
    assert formset.flex_form.fields.count() == 6
    assert formset.flex_form.fields.filter(label="First Name").exists()
    assert formset.flex_form.fields.filter(label="Last Name").exists()
    assert formset.flex_form.fields.filter(label="Date Of Birth").exists()

