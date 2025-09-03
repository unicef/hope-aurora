from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock
from unittest.mock import Mock

import pytest
from django.urls import reverse
from pyquery import PyQuery
from testutils.factories import FormFactory, MessageFactory, RegistrationFactory
from webtest import Upload

from aurora.core import fields

if TYPE_CHECKING:
    from aurora.i18n.models import Message


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.timestamp = datetime.now()
    state.request = Mock(user=AnonymousUser(), headers={"I18N_SESSION": "abc"})
    yield state
    state.request = None
    state.data = {"collect_messages": False, "hit_messages": False}


@pytest.fixture
def registration():
    from aurora.core.cache import cache

    cache.clear()
    frm = FormFactory(name="Form1")
    frm.fields.get_or_create(label="Name", required=True, defaults={"field_type": fields.CharField})
    frm.fields.get_or_create(label="Date Of Birth", required=True, defaults={"field_type": fields.DateField})

    return RegistrationFactory(flex_form=frm, encrypt_data=False)


@pytest.fixture
def record():
    m1 = MessageFactory(msgstr="Name", locale="en-us")
    m1.update_or_create_translation("Nome", "it-it", draft=False)
    MessageFactory(msgstr="Date Of Birth", locale="en-us")
    return m1


@pytest.fixture
def app(db, django_app_factory):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app


def test_i18n_admin_changelist(app, mock_state, record):
    url = reverse("admin:i18n_message_changelist")
    res = app.get(url)
    assert res.status_code == 200, res.location


def test_i18n_admin_change(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    assert res.status_code == 200, res.location


def test_i18n_admin_siblings(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    res = res.click("Siblings")
    assert res.status_code == 302


def test_i18n_admin_create_translation_single_update(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    res = res.click("Create Translation")
    res.forms["translation_form"]["locale"] = "it-it"
    res = res.forms["translation_form"].submit().follow()
    translation: Message = res.context["original"]
    assert record.msgid == translation.msgid
    assert translation.draft
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "Message found."


def test_i18n_admin_create_translation_single_create(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    res = res.click("Create Translation")
    res.forms["translation_form"]["locale"] = "de-de"
    res = res.forms["translation_form"].submit().follow()
    translation: Message = res.context["original"]
    assert record.msgid == translation.msgid
    assert translation.draft
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "Message created."


def test_i18n_admin_create_translation_single_error(app, mock_state, record):
    with mock.patch("aurora.i18n.models.Message.update_or_create_translation", side_effect=Exception()):
        url = reverse("admin:i18n_message_change", args=(record.pk,))
        res = app.get(url)
        res = res.click("Create Translation")
        res.forms["translation_form"]["locale"] = "de-de"
        res = res.forms["translation_form"].submit()
        assert res.status_code == 302


def test_i18n_admin_create_translations(app, mock_state, record):
    url = reverse("admin:i18n_message_changelist")
    res = app.get(url)
    res = res.click("Create Translations")
    res.forms["translation_form"]["locale"] = "it-it"
    res = res.forms["translation_form"].submit()
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "1 messages created. 2 available"

    url = reverse("admin:i18n_message_create_translations")
    res = app.post(url, {})
    assert res.status_code == 200


def test_i18n_admin_create_translations_error(app, mock_state, record):
    url = reverse("admin:i18n_message_changelist")
    with mock.patch("aurora.i18n.models.Message.objects.get_or_create", side_effect=Exception()):
        res = app.get(url)
        res = res.click("Create Translations")
        res.forms["translation_form"]["locale"] = "it-it"
        res = res.forms["translation_form"].submit()
        message = PyQuery(res.text)("ul.messagelist").text()
        assert "Exception" in message


def test_i18n_admin_do_not_create_duplicate_translation(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    res = res.click("Create Translation")
    res.forms["translation_form"]["locale"] = record.locale
    res = res.forms["translation_form"].submit().follow()
    translation: Message = res.context["original"]
    assert record.id == translation.id


def test_i18n_admin_create_invalid(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    res = res.click("Create Translation")
    res.forms["translation_form"]["locale"].force_value("err")
    res = res.forms["translation_form"].submit()
    assert res.status_code == 200


def test_i18n_admin_import_translation(app, mock_state, record):
    from aurora.i18n.models import Message

    url = reverse("admin:i18n_message_import_translations")
    res = app.get(url)
    form = res.forms["importForm"]
    form["locale"] = "it-it"
    form["csv-delimiter"] = ","
    content = Path("tests/data/it_translations.csv").read_bytes()
    form["csv_file"] = Upload("tests/data/it_translations.csv", content)
    res = form.submit()
    assert res.status_code == 200
    form = res.forms["importForm"]
    res = form.submit("save").follow()

    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "Messages processed: Processed: 5, Selected: 5, Created: 4, Updated: 1"

    assert Message.objects.filter(msgid="Date Of Birth", locale="it-it").exists()
    assert Message.objects.filter(msgid="Name", locale="it-it").exists()
    assert Message.objects.filter(msgid="Save", locale="it-it").exists()
    assert Message.objects.filter(msgid="please fix the errors below", locale="it-it").exists()
    assert Message.objects.filter(msgid="required", locale="it-it").exists()


def test_i18n_admin_import_header(app, mock_state, record):
    from aurora.i18n.models import Message

    url = reverse("admin:i18n_message_import_translations")
    res = app.get(url)
    form = res.forms["importForm"]
    form["locale"] = "it-it"
    form["csv-delimiter"] = ","
    form["csv-header"] = True
    content = Path("tests/data/it_translations_header.csv").read_bytes()
    form["csv_file"] = Upload("tests/data/it_translations_header.csv", content)
    res = form.submit()
    assert res.status_code == 200
    form = res.forms["importForm"]
    res = form.submit("save").follow()

    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "Messages processed: Processed: 5, Selected: 5, Created: 4, Updated: 1"

    assert Message.objects.filter(msgid="Date Of Birth", locale="it-it").exists()
    assert Message.objects.filter(msgid="Name", locale="it-it").exists()
    assert Message.objects.filter(msgid="Save", locale="it-it").exists()
    assert Message.objects.filter(msgid="please fix the errors below", locale="it-it").exists()
    assert Message.objects.filter(msgid="required", locale="it-it").exists()


def test_i18n_admin_import_translation_no_selection(app, mock_state, record):
    url = reverse("admin:i18n_message_import_translations")
    res = app.get(url)
    form = res.forms["importForm"]
    form["locale"] = "it-it"
    form["csv-delimiter"] = ","
    content = Path("tests/data/it_translations.csv").read_bytes()
    form["csv_file"] = Upload("tests/data/it_translations.csv", content)
    res = form.submit()
    assert res.status_code == 200
    form = res.forms["importForm"]
    form["selection"] = []
    res = form.submit("save").follow()
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "Messages processed: Processed: 5, Selected: 0, Created: 0, Updated: 0"


def test_i18n_admin_import_translation_error(app, mock_state, record):
    url = reverse("admin:i18n_message_import_translations")
    res = app.get(url)
    form = res.forms["importForm"]
    form["locale"] = "it-it"
    form["csv-delimiter"] = ";"
    content = Path("tests/data/it_translations.csv").read_bytes()
    form["csv_file"] = Upload("tests/data/it_translations.csv", content)
    res = form.submit()
    assert res.status_code == 200
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "Error on line 1. Check import configuration"


def test_i18n_admin_get_or_create(app, mock_state, record, registration):
    url = reverse("admin:i18n_message_get_or_create")
    res = app.get(url)
    assert res.status_code == 302
    res = app.post(url, {"msgid": "First Name", "lang": "it-it"})
    assert res.status_code == 302
    res = app.post(url, {"msgid": "First Name", "lang": "en-us"})
    assert res.status_code == 302


def test_i18n_admin_check_orphans(app, mock_state, record, registration):
    url = reverse("admin:i18n_message_check_orphans")
    res = app.get(url)
    form = res.forms["check-form"]
    form["locale"] = "it-it"
    res = form.submit()
    assert res.status_code == 200


def test_i18n_admin_action_approve(app, mock_state, record, registration):
    url = reverse("admin:i18n_message_changelist")
    res = app.get(url)
    res.forms["changelist-form"]["action"] = "approve"
    res.forms["changelist-form"].get("_selected_action", index=1).value = True
    res = res.forms["changelist-form"].submit("index").follow()
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "1 Messages have been approved"


def test_i18n_admin_action_rehash(app, mock_state, record, registration):
    url = reverse("admin:i18n_message_changelist")
    res = app.get(url)
    res.forms["changelist-form"]["action"] = "rehash"
    res.forms["changelist-form"].get("_selected_action", index=1).value = True
    res = res.forms["changelist-form"].submit("index").follow()
    message = PyQuery(res.text)("ul.messagelist").text()
    assert message == "1 Messages have been rehashed"
