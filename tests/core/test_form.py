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
