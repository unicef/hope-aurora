from datetime import date
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from django.urls import reverse
from testutils.factories import CounterFactory, OrganizationFactory, ProjectFactory, RegistrationFactory, UserFactory
from testutils.perms import user_grant_permissions

from aurora.counters.models import Counter

if TYPE_CHECKING:
    from aurora.registration.models import Registration


@pytest.fixture(autouse=True)
def mock_state():
    from django.contrib.auth.models import AnonymousUser

    from aurora.state import state

    state.request = Mock(user=AnonymousUser())


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
    org = OrganizationFactory()
    prj = ProjectFactory(organization=org, slug="prj")
    reg = RegistrationFactory(project=prj)
    return [CounterFactory(day=date(today.year, today.month, day), registration=reg) for day in range(1, 28)]


@pytest.mark.django_db
def test_counter_index(app, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:index", args=[reg.project.organization.slug])
    res = app.get(url, expect_errors=True)
    assert res.status_code == 403
    with user_grant_permissions(app._user, ["counters.view_counter"], reg):
        res = app.get(url)
        assert res.status_code == 200


@pytest.mark.django_db
def test_counter_project_index(app, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:project-index", args=[reg.project.organization.slug, reg.project.pk])
    res = app.get(url, expect_errors=True)
    assert res.status_code == 403
    with user_grant_permissions(app._user, ["counters.view_counter"], reg):
        res = app.get(url)
        assert res.status_code == 200


@pytest.mark.django_db
def test_counter_registration(app, data):
    reg: "Registration" = data[0].registration

    url = reverse("charts:registration", args=[reg.project.organization.slug, reg.project.pk, reg.pk])
    res = app.get(url, user=None)
    assert res.status_code == 302

    res = app.get(url, expect_errors=True)
    assert res.status_code == 403
    with user_grant_permissions(app._user, ["counters.view_counter"], reg):
        res = app.get(url)
        assert res.status_code == 200


@pytest.mark.django_db
def test_counter_monthly_data(app, data):
    reg: "Registration" = data[0].registration
    url = reverse("charts:monthly_data", args=[reg.project.organization.slug, reg.project.pk, reg.pk])
    res = app.get(url, expect_errors=True)
    assert res.status_code == 403
    with user_grant_permissions(app._user, ["counters.view_counter"], reg):
        res = app.get(url)
        assert res.status_code == 200
        res = app.get(f"{url}?m={data[0].day.strftime('%Y-%m-%d')}")
        assert res.status_code == 200
