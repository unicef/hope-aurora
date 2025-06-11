import base64
import json
import os
from hashlib import md5
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from constance import config
from django.conf import settings
from django.urls import reverse
from django.utils import translation
from testutils.factories import RecordFactory, ValidatorFactory
from testutils.perms import user_grant_permissions
from webtest import Upload

from aurora.state import state

if TYPE_CHECKING:
    from aurora.registration.models import Record

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


@pytest.fixture
def simple_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(flex_form=simple_form, encrypt_data=False)


@pytest.fixture
def unique_last_name_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        encrypt_data=False,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


@pytest.fixture
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


@pytest.fixture
def fernet_encrypted_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=simple_form,
        encrypt_data=True,
        unique_field_path="last_name",
        unique_field_error="last_name is not unique",
    )


@pytest.fixture
def complex_registration(complex_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=complex_form,
        encrypt_data=False,
    )


@pytest.fixture
def james_registration(complex_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(
        name="registration #3",
        flex_form=complex_form,
        unique_field_path="form2s[].[first_name][0][0]",
    )


@pytest.fixture
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


@pytest.mark.django_db
@pytest.mark.mini_racer
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
@pytest.mark.mini_racer
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
@pytest.mark.mini_racer
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
@pytest.mark.mini_racer
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
@pytest.mark.mini_racer
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

    r: Record = res.context["record"]
    assert r.data["form2s"][0]["first_name"] == "First0"
    assert r.data["form2s"][0]["last_name"] == "Last0"
    assert r.data["form2s"][1]["first_name"] == "First1"


@pytest.mark.parametrize("first_name", LANGUAGES.values(), ids=LANGUAGES.keys())
@pytest.mark.mini_racer
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
    record: Record = res.context["record"]
    data = record.decrypt(rsa_encrypted_registration._private_pem)
    assert data["first_name"] == first_name


@pytest.mark.django_db
@pytest.mark.mini_racer
def test_upload_image(django_app, complex_registration, mock_storage):
    url = complex_registration.get_absolute_url()
    res = django_app.get(url)
    res.form["family_name"] = "HH #1"
    content = Path("tests/data/image.png").read_bytes()
    image = Upload("tests/data/image.jpeg", content)
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
            "image": image,
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


@pytest.mark.django_db
@pytest.mark.mini_racer
def test_upload_image_register_rsa_encrypted(django_app, rsa_encrypted_registration, mock_storage):
    url = rsa_encrypted_registration.get_absolute_url()
    content = Path("tests/data/image.png").read_bytes()
    image = Upload("tests/data/image.jpeg", Path("tests/data/image.png").read_bytes())

    res = django_app.get(url)
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res.form["image"] = image

    res = res.form.submit().follow()
    record = res.context["record"]
    data = record.decrypt(rsa_encrypted_registration._private_pem)

    assert data["first_name"] == "first"
    assert data["image"].read().decode() == base64.b64encode(content).decode()


@pytest.mark.django_db
@pytest.mark.mini_racer
def test_upload_image_register_fernet_encrypted(django_app, fernet_encrypted_registration, mock_storage):
    url = fernet_encrypted_registration.get_absolute_url()
    content = Path("tests/data/image.png").read_bytes()
    image = Upload("tests/data/image.jpeg", content)

    res = django_app.get(url)
    res.form["first_name"] = "first"
    res.form["last_name"] = "last"
    res.form["image"] = image
    res.form["file"] = image

    res = res.form.submit().follow()
    record: Record = res.context["record"]

    data = record.decrypt(secret=None)

    assert data["first_name"] == "first"
    assert data["image"].read().decode() == base64.b64encode(content).decode()
    assert data["file"].read().decode() == base64.b64encode(content).decode()


@pytest.mark.django_db
@pytest.mark.mini_racer
def test_register_protected_registration(django_app, user, protected_registration):
    from testutils.perms import user_grant_permissions

    url = protected_registration.get_absolute_url()
    res = django_app.get(url)
    assert res.status_code == 302
    assert res.headers["location"].startswith("/login?next=")
    with user_grant_permissions(user, "registration.register", protected_registration):
        res = django_app.get(url, user=user.username)
    assert res.status_code == 200


@pytest.mark.django_db
def test_registration_data_view_registration_property(simple_registration):
    from aurora.registration.views.data import RegistrationDataView
    from django.http import Http404

    view = RegistrationDataView()
    view.kwargs = {"slug": simple_registration.slug}
    assert view.registration == simple_registration

    view = RegistrationDataView()
    view.kwargs = {"pk": simple_registration.pk}
    assert view.registration == simple_registration

    view = RegistrationDataView()
    view.kwargs = {}
    with pytest.raises(Http404):
        _ = view.registration

    view = RegistrationDataView()
    view.kwargs = {"slug": "non-existent-slug"}
    with pytest.raises(Http404):
        _ = view.registration


@pytest.mark.django_db
def test_registrations_view_get(django_app, simple_registration):
    url = reverse("registrations")
    res = django_app.get(url)
    assert res.status_code == 200
    assert simple_registration.name in res.text


@pytest.mark.django_db
def test_registrations_view_post(django_app, simple_registration, complex_registration):
    url = reverse("registrations")
    from aurora.registration.models import Registration

    assert not Registration.objects.filter(is_pwa_enabled=True).exists()

    res = django_app.get(url)
    form = res.form
    form["slug"] = simple_registration.slug
    res = form.submit()
    assert res.status_code == 200
    assert simple_registration.name in res.text

    simple_registration.refresh_from_db()
    assert simple_registration.is_pwa_enabled is True

    res = django_app.get(url)
    form = res.form
    form["slug"] = complex_registration.slug
    res = form.submit()
    assert res.status_code == 200
    assert complex_registration.name in res.text

    simple_registration.refresh_from_db()
    complex_registration.refresh_from_db()
    assert simple_registration.is_pwa_enabled is False
    assert complex_registration.is_pwa_enabled is True


@pytest.mark.django_db
def test_get_pwa_enabled(django_app, simple_registration):
    url = reverse("get_pwa_enabled")

    res = django_app.get(url)
    assert res.status_code == 200
    data = res.json
    assert data["slug"] is None
    assert data["version"] is None
    assert data["publicKey"] is None
    assert data["optionsSets"] is None

    simple_registration.is_pwa_enabled = True
    simple_registration.save(update_fields=["is_pwa_enabled"])

    res = django_app.get(url)
    assert res.status_code == 200
    data = res.json
    assert data["slug"] == simple_registration.slug
    assert data["version"] == simple_registration.version
    assert data["publicKey"] == simple_registration.public_key
    assert data["optionsSets"] == simple_registration.option_set_links


@pytest.mark.django_db
def test_authorize_cookie(django_app, user):
    from django.core import signing
    import json

    url = reverse("authorize_cookie")

    signed_data = signing.dumps(
        {"_auth_user_id": user.id},
        salt="django.contrib.sessions.backends.signed_cookies"
    )
    res = django_app.post(url, json.dumps(signed_data), content_type="application/json")
    assert res.status_code == 200
    assert res.json["authorized"] is True

    signed_data = signing.dumps(
        {"_auth_user_id": 999999},
        salt="django.contrib.sessions.backends.signed_cookies"
    )
    res = django_app.post(url, json.dumps(signed_data), content_type="application/json")
    assert res.status_code == 200
    assert res.json["authorized"] is False

    res = django_app.post(url, "invalid json", content_type="application/json")
    assert res.status_code == 200
    assert res.json["authorized"] is False

    res = django_app.post(url, "invalid signature", content_type="application/json")
    assert res.status_code == 200
    assert res.json["authorized"] is False


@pytest.mark.django_db
def test_registrations_view_unsupported_method(django_app):
    url = reverse("registrations")

    res = django_app.head(url, expect_errors=True)
    assert res.status_code == 405

    res = django_app.options(url, expect_errors=True)
    assert res.status_code == 405


@pytest.mark.django_db
def test_register_auth_view(django_app, simple_registration, user):
    url = reverse("register-auth", kwargs={"slug": simple_registration.slug})

    res = django_app.get(url)
    assert res.status_code == 200
    data = res.json
    assert data["registration"]["name"] == simple_registration.name
    assert data["registration"]["locale"] == simple_registration.locale
    assert data["registration"]["protected"] == simple_registration.protected
    assert data["project"]["build_date"] == os.environ.get("BUILD_DATE", "")
    assert data["project"]["version"] == os.environ.get("VERSION", "")
    assert data["project"]["debug"] == settings.DEBUG
    assert data["project"]["env"] == settings.SMART_ADMIN_HEADER
    assert data["project"]["sentry_dsn"] == settings.SENTRY_DSN
    assert data["project"]["cache"] == config.CACHE_VERSION
    assert "has_token" in data["project"]
    assert data["user"]["username"] == ""
    assert data["user"]["anonymous"] is True

    res = django_app.get(url, user=user.username)
    assert res.status_code == 200
    data = res.json
    assert data["user"]["username"] == user.username
    assert data["user"]["anonymous"] is False

    simple_registration.active = False
    simple_registration.save(update_fields=["active"])

    user.is_staff = True
    user.save(update_fields=["is_staff"])
    res = django_app.get(url, user=user.username)
    assert res.status_code == 200

    user.is_staff = False
    user.save(update_fields=["is_staff"])
    res = django_app.get(url, user=user.username, expect_errors=True)
    assert res.status_code == 404

    url = reverse("register-auth", kwargs={"slug": "non-existent"})
    res = django_app.get(url, expect_errors=True)
    assert res.status_code == 404


@pytest.mark.django_db
def test_qr_verify(django_app, simple_registration):
    mock_request = Mock()
    mock_request.META = {"REMOTE_ADDR": "127.0.0.1"}
    state.request = mock_request

    record = RecordFactory(registration=simple_registration, storage=b"test storage")

    correct_hash = md5(record.storage).hexdigest()

    url = reverse("register-verify", kwargs={"pk": record.pk, "hash": correct_hash})
    res = django_app.get(url)
    assert res.status_code == 200
    assert res.context["valid"] is True
    assert res.context["record"] == record

    incorrect_hash = "incorrect_hash"
    url = reverse("register-verify", kwargs={"pk": record.pk, "hash": incorrect_hash})
    res = django_app.get(url)
    assert res.status_code == 200
    assert res.context["valid"] is False
    assert res.context["record"] == record


@pytest.mark.django_db
@patch('aurora.registration.views.registration.state')
def test_register_complete_view_record_not_found(mock_state, django_app, simple_registration):
    mock_state.collect_messages = False
    url = reverse("register-done", kwargs={"reg": simple_registration.pk, "rec": 999999})
    res = django_app.get(url, expect_errors=True)
    assert res.status_code == 404

    mock_state.collect_messages = True
    url = reverse("register-done", kwargs={"reg": simple_registration.pk, "rec": 999999})
    res = django_app.get(url, expect_errors=True)
    assert res.status_code == 404


@pytest.mark.django_db
def test_register_complete_view_context_data(django_app, simple_registration):
    from constance.test import override_config
    from aurora.core.utils import get_qrcode

    record = RecordFactory(registration=simple_registration)
    url = reverse("register-done", kwargs={"reg": simple_registration.pk, "rec": record.pk})

    with override_config(QRCODE=True):
        res = django_app.get(url)
        assert res.status_code == 200
        context = res.context
        assert context["record"] == record
        assert context["registration_url"] == simple_registration.get_absolute_url()
        assert context["qrcode"] is not None
        assert context["url"] is not None

        expected_hash = md5(str(record.fields).encode()).hexdigest()
        base_url = f"http://testserver{url}"
        expected_url = f"{base_url}/{expected_hash}"
        assert context["url"] == base_url
        assert context["qrcode"] == get_qrcode(expected_url)

    with override_config(QRCODE=False):
        res = django_app.get(url)
        assert res.status_code == 200
        context = res.context
        assert context["record"] == record
        assert context["registration_url"] == simple_registration.get_absolute_url()
        assert context["qrcode"] is None
        assert context["url"] is None


@pytest.mark.django_db
def test_register_router(django_app, simple_registration):
    url = reverse("registration-router")

    res = django_app.post(url, {"slug": simple_registration.slug})
    assert res.status_code == 302
    assert res.headers["location"].startswith(f"/en-us/register/{simple_registration.slug}/1/")

    res = django_app.post(url, {"slug": "non-existent"}, expect_errors=True)
    assert res.status_code == 404

    simple_registration.locales = ["fr", "de"]
    simple_registration.locale = "fr"
    simple_registration.save(update_fields=["locales", "locale"])

    with translation.override("en"):
        res = django_app.post(url, {"slug": simple_registration.slug})
        assert res.status_code == 302
        assert res.headers["location"].startswith(f"/fr/register/{simple_registration.slug}/1/")

    with translation.override("de"):
        res = django_app.post(url, {"slug": simple_registration.slug})
        assert res.status_code == 302
        assert res.headers["location"].startswith(f"/fr/register/{simple_registration.slug}/1/")


@pytest.mark.django_db
def test_register_router_methods(django_app):
    from aurora.registration.views.registration import RegisterRouter
    from django.forms import Form

    view = RegisterRouter()
    assert view.get_template_names() == []

    assert view.get_form() is None
    assert view.get_form(Form) is None


@pytest.mark.django_db
def test_register_view_get(django_app, simple_registration):
    from aurora.state import state
    from django.utils import translation
    from django.urls import reverse

    url = reverse("register", kwargs={"slug": simple_registration.slug})

    state.collect_messages = True
    res = django_app.get(url)
    assert res.status_code == 200
    assert "ETag" in res.headers
    state.collect_messages = False

    simple_registration.locales = ["fr", "de"]
    simple_registration.locale = "fr"
    simple_registration.save(update_fields=["locales", "locale"])

    with translation.override("en"):
        res = django_app.get(url)
        assert res.status_code == 302
        assert res.headers["location"].startswith(f"/fr/register/{simple_registration.slug}/1/")

    with translation.override("de"):
        res = django_app.get(url)
        assert res.status_code == 302
        assert res.headers["location"].startswith(f"/fr/register/{simple_registration.slug}/1/")


@pytest.mark.django_db
def test_register_view_check_access(django_app, simple_registration, user):
    url = reverse("register", kwargs={"slug": simple_registration.slug})

    simple_registration.protected = True
    simple_registration.save(update_fields=["protected"])
    res = django_app.get(url)
    assert res.status_code == 302
    assert res.headers["location"].startswith("/login?next=")

    res = django_app.get(url, user=user.username)
    assert res.status_code == 302
    assert res.headers["location"].startswith("/login?next=")
