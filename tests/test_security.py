import pytest

from aurora.security.backend import AuroraAuthBackend


@pytest.fixture()
def simple_registration(simple_form):
    from aurora.registration.models import Registration

    reg, __ = Registration.objects.get_or_create(
        locale="en-us",
        name="registration #1",
        defaults={"flex_form": simple_form, "encrypt_data": False, "active": True},
    )
    return reg


def test_smartbackend_allow(db, user):
    s = AuroraAuthBackend()
    assert not s.has_perm(user, "registration_registration.create_translation")


def test_smartbackend_reg(db, user, simple_registration):
    s = AuroraAuthBackend()
    assert not s.has_perm(user, "registration_registration.create_translation", simple_registration)
