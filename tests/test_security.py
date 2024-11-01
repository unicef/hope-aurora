import pytest
from testutils.perms import user_grant_permissions

from aurora.registration.models import Registration
from aurora.security.backend import AuroraAuthBackend


@pytest.fixture()
def simple_registration(simple_form):
    from testutils.factories import RegistrationFactory

    return RegistrationFactory(name="Registration-#1")


def test_smartbackend_allow(db, user):
    s = AuroraAuthBackend()
    assert not s.has_perm(user, "registration_registration.create_translation")


def test_smartbackend_reg(db, user, simple_registration):
    s = AuroraAuthBackend()
    assert not s.has_perm(user, "registration_registration.create_translation", simple_registration)


def test_roles(db, user, simple_registration: Registration):
    s = AuroraAuthBackend()
    with user_grant_permissions(user, "counters.view_counter", simple_registration):
        assert s.has_perm(user, "counters.view_counter", simple_registration)
        assert s.has_perm(user, "counters.view_counter", simple_registration.project)
        assert s.has_perm(user, "counters.view_counter", simple_registration.project.organization)
    with user_grant_permissions(user, "counters.view_counter", simple_registration.project):
        assert not s.has_perm(user, "counters.view_counter", simple_registration)
        assert s.has_perm(user, "counters.view_counter", simple_registration.project)
        assert s.has_perm(user, "counters.view_counter", simple_registration.project.organization)
    with user_grant_permissions(user, "counters.view_counter", simple_registration.project.organization):
        assert not s.has_perm(user, "counters.view_counter", simple_registration)
        assert not s.has_perm(user, "counters.view_counter", simple_registration.project)
        assert s.has_perm(user, "counters.view_counter", simple_registration.project.organization)
