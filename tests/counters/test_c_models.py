from datetime import date
from typing import TYPE_CHECKING

import pytest
from django.test import RequestFactory
from testutils.factories import (
    RecordFactory,
    RegistrationFactory,
    UserFactory,
)

from aurora.counters.models import Counter

if TYPE_CHECKING:
    from aurora.registration.models import Registration


@pytest.fixture(autouse=True)
def mock_state(rf: RequestFactory):
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = rf.get("/", user=AnonymousUser())


@pytest.fixture
def app(django_app_factory):
    user = UserFactory(username="user")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(user)
    django_app._user = user
    return django_app


@pytest.fixture
def data(db) -> list[Counter]:
    today = date.today()
    reg = RegistrationFactory()
    return [RecordFactory(timestamp=date(today.year, today.month, day), registration=reg) for day in range(1, 28)]


def test_collect(data):
    assert Counter.objects.collect()


def test_collect_reg(data):
    reg: "Registration" = data[0].registration

    assert Counter.objects.collect(registrations=[reg.pk])
