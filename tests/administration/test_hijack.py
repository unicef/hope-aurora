from unittest import mock

import pytest
from django.urls import reverse

from aurora.administration.hijack import impersonate


@pytest.fixture
def app(django_app_factory):
    return django_app_factory(csrf_checks=False)


def test_impersonate(user, admin_user):
    with mock.patch("aurora.administration.hijack.can_hijack", return_value=True):
        assert impersonate(admin_user, user) is None


def test_hijack_security(app, user, admin_user):
    url = reverse("admin:security_user_hijack", args=(user.id,))
    with mock.patch("aurora.security.admin.is_root", return_value=False):
        res = app.get(url, user=admin_user, expect_errors=True)
        assert res.status_code == 403


def test_hijack(app, user, admin_user):
    url = reverse("admin:security_user_change", args=(user.id,))
    with mock.patch("aurora.security.admin.is_root", return_value=True):
        res = app.get(url, user=admin_user)
        res = res.click("Hijack").follow().follow()
        assert f"You are authenticated as {user.username}" in res.text
        res = res.forms[1].submit().follow().follow()
        assert f">{admin_user.username}</" in res.text
