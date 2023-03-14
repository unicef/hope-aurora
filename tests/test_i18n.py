import pytest
from django.urls import reverse


@pytest.fixture()
def simple_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        encrypt_data=False,
    )
    # from aurora.registration.models import Registration
    #
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us",
    #     name="registration #1",
    #     defaults={"flex_form": simple_form, "encrypt_data": False, "active": True},
    # )
    # return reg


@pytest.mark.django_db
def test_register_simple(django_app, simple_registration):
    url = reverse("register", args=[simple_registration.slug, simple_registration.version])
    assert url == f"/en-us/register/{simple_registration.slug}/{simple_registration.version}/"
    res = django_app.get(url)
    res = res.form.submit()
    res.form["first_name"] = "first_name"
    res.form["last_name"] = "f"
    res = res.form.submit()
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res = res.form.submit().follow()
    assert res.context["record"].data["first_name"] == "first"


@pytest.mark.django_db
def test_create_translation(django_app, simple_registration, admin_user):
    url = reverse("admin:registration_registration_create_translation", args=[simple_registration.pk])
    # assert url == f"/en-us/register/registration-1/{simple_registration.version}/"
    res = django_app.get(url, user=admin_user)
    # translation-form
    res = res.form.submit()
    # res = res.form.submit()
    # res.form["first_name"] = "first_name"
    # res.form["last_name"] = "f"
    # res = res.form.submit()
    # res.form["first_name"] = "first"
    # res.form["last_name"] = "last"
    # res = res.form.submit().follow()
    # assert res.context["record"].data["first_name"] == "first"
