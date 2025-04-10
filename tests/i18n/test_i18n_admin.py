from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from django.urls import reverse
from testutils.factories import FormFactory, MessageFactory, RegistrationFactory

from aurora.core import fields

if TYPE_CHECKING:
    from aurora.i18n.models import Message


@pytest.fixture
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

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
    m1 = MessageFactory(msgstr="name", locale="en-us")
    m1.update_or_create_translation("nome", "it", draft=False)
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


def test_i18n_admin_create_translation(app, mock_state, record):
    url = reverse("admin:i18n_message_change", args=(record.pk,))
    res = app.get(url)
    res = res.click("Create Translation")
    res.forms["translation_form"]["locale"] = "it-it"
    res = res.forms["translation_form"].submit().follow()
    translation: Message = res.context["original"]
    assert record.msgid == translation.msgid
    assert translation.draft


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
