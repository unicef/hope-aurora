from unittest import mock

import pytest
from django.urls import reverse

from aurora.administration.hijack import can_impersonate, impersonate


@pytest.fixture
def app(django_app_factory):
    return django_app_factory(csrf_checks=False)


def test_impersonate(user, admin_user, rf):
    req = rf.get("/")
    req.user = admin_user
    with mock.patch("aurora.administration.hijack.can_hijack", return_value=False):
        assert impersonate(req, user) is None


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


def test_can_impersonate_requires_staff_and_superuser(user):
    from testutils.factories import UserFactory

    regular = UserFactory()
    regular.is_hijacked = False
    assert can_impersonate(hijacker=regular, hijacked=user) is False


def test_can_impersonate_staff_only(user):
    from testutils.factories import UserFactory

    staff_only = UserFactory(is_staff=True, is_superuser=False)
    staff_only.is_hijacked = False
    assert can_impersonate(hijacker=staff_only, hijacked=user) is False


def test_can_impersonate_superuser_only(user):
    from testutils.factories import UserFactory

    super_only = UserFactory(is_staff=False, is_superuser=True)
    super_only.is_hijacked = False
    assert can_impersonate(hijacker=super_only, hijacked=user) is False


def test_can_impersonate_staff_and_superuser(user):
    from testutils.factories import SuperUserFactory

    staff_super = SuperUserFactory()
    staff_super.is_hijacked = False
    assert can_impersonate(hijacker=staff_super, hijacked=user) is True


def test_can_impersonate_self_blocked(db):
    from testutils.factories import SuperUserFactory

    staff_super = SuperUserFactory()
    staff_super.is_hijacked = False
    assert can_impersonate(hijacker=staff_super, hijacked=staff_super) is False


def test_can_impersonate_rejects_already_hijacked(user):
    from testutils.factories import SuperUserFactory

    staff_super = SuperUserFactory()
    staff_super.is_hijacked = True
    assert can_impersonate(hijacker=staff_super, hijacked=user) is False


def test_acquire_endpoint_rejects_regular_user(app, user):
    from testutils.factories import UserFactory

    regular = UserFactory()
    url = reverse("hijack:acquire")
    res = app.post(url, {"user_pk": user.pk}, user=regular, expect_errors=True)
    assert res.status_code == 403


def test_acquire_endpoint_rejects_staff_only(app, user):
    from testutils.factories import UserFactory

    staff_only = UserFactory(is_staff=True, is_superuser=False)
    url = reverse("hijack:acquire")
    res = app.post(url, {"user_pk": user.pk}, user=staff_only, expect_errors=True)
    assert res.status_code == 403


def test_acquire_endpoint_rejects_superuser_only(app, user):
    from testutils.factories import UserFactory

    super_only = UserFactory(is_staff=False, is_superuser=True)
    url = reverse("hijack:acquire")
    res = app.post(url, {"user_pk": user.pk}, user=super_only, expect_errors=True)
    assert res.status_code == 403


def test_acquire_endpoint_allows_staff_and_superuser(app, user):
    from testutils.factories import SuperUserFactory

    staff_super = SuperUserFactory()
    url = reverse("hijack:acquire")
    res = app.post(url, {"user_pk": user.pk}, user=staff_super)
    assert res.status_code == 302
