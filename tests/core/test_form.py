import pytest


@pytest.mark.django_db
def test_create_form(db):
    from testutils.factories import FormFactory

    form = FormFactory(name="test")
    assert form


@pytest.mark.django_db
def test_fixed_formset(db):
    from testutils.factories import FormFactory

    master = FormFactory(name="Master")
    detail = FormFactory(name="Detail")
    fs = master.add_formset(detail, extra=1, dynamic=False)
    assert fs.name == "details"


@pytest.mark.django_db
def test_add_formset(db):
    from testutils.factories import FormFactory

    master = FormFactory(name="Master")
    detail = FormFactory(name="Detail")
    fs = master.add_formset(detail)
    assert fs.name == "details"


@pytest.mark.django_db
def test_version_update(db):
    from testutils.factories import FlexFormFieldFactory, RegistrationFactory

    registration = RegistrationFactory()
    flex_form = registration.flex_form
    form_ver = flex_form.version
    reg_ver = registration.version
    FlexFormFieldFactory(flex_form=flex_form, label="New Field")
    flex_form.refresh_from_db()
    registration.refresh_from_db()
    assert flex_form.version == form_ver + 1, "FlexForm version should increment."
    assert registration.version == reg_ver + 1, "Registration version should increment."
