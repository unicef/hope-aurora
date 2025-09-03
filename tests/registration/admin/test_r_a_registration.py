import pytest
from django.urls import reverse
from pyquery import PyQuery
from testutils.factories import RecordFactory

from aurora.registration.models import Registration


@pytest.fixture
def flex_form(db):
    from testutils.factories import FormFactory

    return FormFactory(name="Form1")


@pytest.fixture
def records(registration):
    return RecordFactory.create_batch(100, files=None, registration=registration)


@pytest.fixture
def registration(flex_form) -> Registration:
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=flex_form,
        encrypt_data=False,
        export_allowed=True,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


@pytest.fixture
def app(django_app_factory, db):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app


def test_registration_add(app, flex_form):
    url = reverse("admin:registration_registration_add")
    res = app.get(url)
    form = res.forms["registration_form"]
    form["name"] = "Registration #1"
    form["project"].force_value(flex_form.project.pk)
    form["flex_form"].force_value(flex_form.pk)
    form.submit()
    assert Registration.objects.filter(name="Registration #1").exists()


def test_registration_export_as_csv(app, registration, records):
    url = reverse("admin:registration_registration_export_as_csv", args=(registration.id,))
    res = app.get(url)
    res.forms["export-form"]["filters"] = "id__lt=0"
    res = res.forms["export-form"].submit()
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "No records matching filtering criteria"
    res.forms["export-form"]["filters"] = "id__gt=0"
    res = res.forms["export-form"].submit()
    uid = PyQuery(res.text)("#results tbody tr:first-child td:first-child").text()
    assert uid == records[0].unicef_id
    res = res.forms["export-form"].submit("export")
    assert res.headers["Content-Type"] == "text/csv"
    assert res.headers["Content-Disposition"]


def test_registration_export_as_csv_with_options(app, registration, records):
    url = reverse("admin:registration_registration_export_as_csv", args=(registration.id,))
    res = app.get(url)
    res.forms["export-form"]["filters"] = "id__gt=0"
    res.forms["export-form"]["include"] = "last_name"
    res.forms["export-form"]["exclude"] = "first_name"
    res.forms["export-form"]["csv-header"] = True
    res = res.forms["export-form"].submit()
    uid = PyQuery(res.text)("#results tbody tr:first-child td:first-child").text()
    assert uid == records[0].fields["last_name"]
    res = res.forms["export-form"].submit("export")
    assert res.headers["Content-Type"] == "text/csv"
    assert res.headers["Content-Disposition"]
