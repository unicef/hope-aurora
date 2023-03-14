import base64
import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from webtest import Upload

LANGUAGES = {
    "english": "first",
    "ukrainian": "АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬьЮюЯя",
    "chinese": "姓名",
    "japanese": "ファーストネーム",
    "arabic": "الاسم الأول",
}


@pytest.fixture(autouse=True)
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())


@pytest.fixture()
def simple_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(flex_form=simple_form, encrypt_data=False)
    # from aurora.registration.models import Registration
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us",
    #     name="registration #1",
    #     defaults={"flex_form": simple_form, "encrypt_data": False, "active": True},
    #     project = Project
    # )
    # return reg


@pytest.fixture()
def unique_last_name_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )
    # from aurora.registration.models import Registration
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us",
    #     name="registration #3",
    #     defaults={
    #         "flex_form": simple_form,
    #         "unique_field_path": "last_name",
    #         "unique_field_error": "last_name is not unique",
    #         "encrypt_data": False,
    #         "active": True,
    #     },
    # )
    # return reg


#


@pytest.fixture()
def rsa_encrypted_registration(simple_form):
    from testutils.factories import RegistrationFactory

    reg = RegistrationFactory(
        name="registration #1",
        flex_form=simple_form,
        encrypt_data=False,
    )
    priv, pub = reg.setup_encryption_keys()
    reg._private_pem = priv
    return reg
    # from aurora.registration.models import Registration
    #
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us",
    #     name="registration #1",
    #     defaults={"flex_form": simple_form, "encrypt_data": False, "active": True},
    # )
    # priv, pub = reg.setup_encryption_keys()
    # reg._private_pem = priv
    # return reg


@pytest.fixture()
def fernet_encrypted_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        encrypt_data=True,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )

    # from aurora.registration.models import Registration
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us", name="registration #3", encrypt_data=True, flex_form=simple_form, active=True
    # )
    # return reg


@pytest.fixture()
def complex_registration(complex_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=complex_form,
        encrypt_data=False,
    )
    # from aurora.registration.models import Registration
    #
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us", name="registration #2", defaults={"flex_form": complex_form, "active": True}
    # )
    # return reg


@pytest.fixture()
def james_registration(complex_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=complex_form,
        unique_field_path="form2s[].[first_name][0][0]",
    )
    # from aurora.registration.models import Registration
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us",
    #     name="registration #2",
    #     unique_field_path="form2s[].[first_name][0][0]",
    #     unique_field_error="xxx must be unique",
    #     defaults={"flex_form": complex_form, "active": True},
    # )
    # return reg


@pytest.fixture()
def protected_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
        encrypt_data=False,
        active=True,
        protected=True,
    )

    # from aurora.registration.models import Registration
    # reg, __ = Registration.objects.get_or_create(
    #     locale="en-us",
    #     name="registration #3",
    #     defaults={
    #         "flex_form": simple_form,
    #         "unique_field_path": "last_name",
    #         "unique_field_error": "last_name is not unique",
    #         "encrypt_data": False,
    #         "active": True,
    #         "protected": True,
    #     },
    # )
    # return reg


@pytest.mark.django_db
def test_register_simple(django_app, simple_registration):
    url = simple_registration.get_absolute_url()
    res = django_app.get(url)
    res = res.form.submit()
    res.form["first_name"] = "first_name"
    res.form["last_name"] = "f"
    res = res.form.submit()
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res.form["time_0"] = "Thu May 12 2022 15:35:36 GMT+0200 (Central European Summer Time)"
    res.form["time_1"] = "2000"
    res.form["time_2"] = "1"
    res.form["time_3"] = "2000"

    res = res.form.submit().follow()
    assert res.context["record"].data["first_name"] == "first"
    assert res.context["record"].counters == {
        "start": "Thu May 12 2022 15:35:36 GMT+0200 (Central European Summer Time)",
        "elapsed": "2000",
        "rounds": "1",
        "total": "2000",
    }


@pytest.mark.django_db
def test_register_indexed(django_app, simple_registration):
    url = simple_registration.get_absolute_url()
    res = django_app.get(url)
    res = res.form.submit()
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"

    res = res.form.submit().follow()
    assert res.context["record"].data["last_name"] == "last"
    assert res.context["record"].index1 == "last"
    assert res.context["record"].index2 is None
    assert res.context["record"].index3 is None


@pytest.mark.django_db
def test_register_unique(django_app, unique_last_name_registration):
    url = unique_last_name_registration.get_absolute_url()
    res = django_app.get(url)
    res = res.form.submit()
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res = res.form.submit().follow()
    assert res.context["record"].data["first_name"] == "first"
    assert res.context["record"].data["last_name"] == "last"
    assert res.context["record"].unique_field == "last"

    res = django_app.get(url)
    res = res.form.submit()
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res = res.form.submit()
    assert res.context["errors"][0].message == unique_last_name_registration.unique_field_error


@pytest.mark.django_db
def test_register_unique_nested(django_app, james_registration):
    url = james_registration.get_absolute_url()
    res = django_app.get(url)
    res = res.form.submit()
    res.form["family_name"] = "Fam #1"
    res.form["form2s-0-first_name"] = "First0"
    res.form["form2s-0-last_name"] = "Last0"
    res.form["form2s-0-date_of_birth"] = "2000-12-01"
    add_extra_form_to_formset_with_data(
        res.form,
        "form2s",
        {
            "first_name": "First1",
            "last_name": "Last1",
            "date_of_birth": "2000-12-01",
        },
    )
    res = res.form.submit()
    assert res.status_code == 302, res.context["form"].errors
    res = res.follow()
    assert res.context["record"].data["form2s"][0]["first_name"] == "First0"
    assert res.context["record"].unique_field == "First0"

    res = django_app.get(url)
    res = res.form.submit()
    res.form["family_name"] = "Fam #1"
    res.form["form2s-0-first_name"] = "First0"
    res.form["form2s-0-last_name"] = "Last0"
    res.form["form2s-0-date_of_birth"] = "2000-12-01"

    # add_extra_form_to_formset_with_data(
    #     res.form,
    #     "form2s",
    #     {
    #         "first_name": "First1",
    #         "last_name": "Last",
    #         "date_of_birth": "2000-12-01",
    #     },
    # )
    res = res.form.submit()
    assert res.context["errors"][0].message == james_registration.unique_field_error


def add_dynamic_field(form, name, value):
    """Add an extra text field to a form. More work required to support files"""
    from webtest.forms import Text

    field = Text(form, "input", None, None, value)
    form.fields[name] = [field]
    form.field_order.append((name, field))


def add_extra_form_to_formset_with_data(form, prefix, field_names_and_values):
    from webtest.forms import Field as WebTestField

    total_forms_field_name = prefix + "-TOTAL_FORMS"
    next_form_index = int(form[total_forms_field_name].value)
    for extra_field_name, extra_field_value in field_names_and_values.items():
        input_field_name = "-".join((prefix, str(next_form_index), extra_field_name))
        extra_field = WebTestField(form, tag="input", name=input_field_name, pos=0, value=extra_field_value)
        form.fields[input_field_name] = [extra_field]
        form[input_field_name] = extra_field_value
        form.field_order.append((input_field_name, extra_field))
        form[total_forms_field_name].value = str(next_form_index + 1)
    return form


@pytest.mark.django_db
def test_register_complex(django_app, complex_registration):
    url = complex_registration.get_absolute_url()
    res = django_app.get(url)
    res.form["family_name"] = "HH #1"
    res.form["form2s-0-first_name"] = "First0"
    res.form["form2s-0-last_name"] = "Last0"
    res.form["form2s-0-date_of_birth"] = "2000-12-01"

    add_extra_form_to_formset_with_data(
        res.form,
        "form2s",
        {
            "first_name": "First1",
            "last_name": "Last1",
            "date_of_birth": "2000-12-01",
        },
    )
    add_extra_form_to_formset_with_data(
        res.form,
        "form2s",
        {
            "first_name": "First2",
            "last_name": "Last",
            "date_of_birth": "2000-12-01",
        },
    )
    res = res.form.submit()
    assert res.status_code == 302, res.context["form"].errors
    res = res.follow()
    from aurora.registration.models import Record

    r: Record = res.context["record"]
    assert r.data["form2s"][0]["first_name"] == "First0"
    assert r.data["form2s"][0]["last_name"] == "Last0"
    assert r.data["form2s"][1]["first_name"] == "First1"


@pytest.mark.parametrize("first_name", LANGUAGES.values(), ids=LANGUAGES.keys())
def test_register_encrypted(django_app, first_name, rsa_encrypted_registration):
    url = rsa_encrypted_registration.get_absolute_url()
    res = django_app.get(url)
    res = res.form.submit()
    res.form["first_name"] = first_name
    res.form["last_name"] = "f"
    res = res.form.submit()
    res.form["first_name"] = first_name
    res.form["last_name"] = "last"
    res = res.form.submit().follow()
    record = res.context["record"]
    data = record.decrypt(rsa_encrypted_registration._private_pem)
    assert data["first_name"] == first_name


@pytest.mark.django_db
def test_upload_image(django_app, complex_registration, mock_storage):
    url = complex_registration.get_absolute_url()
    res = django_app.get(url)
    res.form["family_name"] = "HH #1"
    # IMAGE = Upload("tests/data/image.jpeg", Path("tests/data/image.png").read_bytes())
    # IMAGE = SimpleUploadedFile("tests/data/image.jpeg", Path("tests/data/image.png").read_bytes())
    content = Path("tests/data/image.png").read_bytes()
    IMAGE = Upload("tests/data/image.jpeg", content)
    res.form["form2s-0-first_name"] = "First0"
    res.form["form2s-0-last_name"] = "Last0"
    res.form["form2s-0-date_of_birth"] = "2000-12-01"

    add_extra_form_to_formset_with_data(
        res.form,
        "form2s",
        {
            "first_name": "First1",
            "last_name": "Last",
            "date_of_birth": "2000-12-01",
            "image": IMAGE,
        },
    )
    res = res.form.submit()
    assert res.status_code == 302, res.context["form"].errors
    res = res.follow()
    obj = res.context["record"]
    assert obj.data["family_name"] == "HH #1"
    assert obj.data["form2s"][1]["image"] == base64.b64encode(content).decode()
    ff = json.loads(obj.files.tobytes().decode())
    assert ff["form2s"][1]["image"] == base64.b64encode(content).decode()
    # from aurora.registration.models import Record
    #
    # r: Record = res.context["record"]
    # assert r.data["family_name"] == "HH #1"
    # assert r.data["form2s"][0]["image"].read().decode() == base64.b64encode(content).decode()


@pytest.mark.django_db
def test_upload_image_register_rsa_encrypted(django_app, rsa_encrypted_registration, mock_storage):
    url = rsa_encrypted_registration.get_absolute_url()
    content = Path("tests/data/image.png").read_bytes()
    IMAGE = Upload("tests/data/image.jpeg", Path("tests/data/image.png").read_bytes())

    res = django_app.get(url)
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res.form["image"] = IMAGE

    res = res.form.submit().follow()
    record = res.context["record"]
    data = record.decrypt(rsa_encrypted_registration._private_pem)

    assert data["first_name"] == "first"
    assert data["image"].read().decode() == base64.b64encode(content).decode()


@pytest.mark.django_db
def test_upload_image_register_fernet_encrypted(django_app, fernet_encrypted_registration, mock_storage):
    from aurora.registration.models import Record

    url = fernet_encrypted_registration.get_absolute_url()
    content = Path("tests/data/image.png").read_bytes()
    IMAGE = Upload("tests/data/image.jpeg", content)

    res = django_app.get(url)
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res.form["image"] = IMAGE
    res.form["file"] = IMAGE

    res = res.form.submit().follow()
    record: Record = res.context["record"]

    data = record.decrypt(secret=None)

    assert data["first_name"] == "first"
    assert data["image"].read().decode() == base64.b64encode(content).decode()
    assert data["file"].read().decode() == base64.b64encode(content).decode()


@pytest.mark.django_db
def test_register_protected_registration(django_app, user, protected_registration):
    from testutils.perms import user_grant_permissions

    url = protected_registration.get_absolute_url()
    res = django_app.get(url)
    assert res.status_code == 302
    assert res.headers["location"].startswith("/login?next=")
    with user_grant_permissions(user, "registration.register", protected_registration):
        res = django_app.get(url, user=user.username)
    assert res.status_code == 200
