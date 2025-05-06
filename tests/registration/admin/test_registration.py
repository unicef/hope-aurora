import pytest
from django.urls import reverse

from aurora.registration.models import Registration


@pytest.fixture
def flex_form(db):
    from testutils.factories import FormFactory

    return FormFactory(name="Form1")


@pytest.fixture
def registration(flex_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=flex_form,
        encrypt_data=False,
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
