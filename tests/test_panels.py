import pytest
from django.contrib.admin.sites import site
from django.urls import reverse

pytestmark = pytest.mark.admin


@pytest.fixture
def app(django_app_factory):
    return django_app_factory(csrf_checks=False)


def pytest_generate_tests(metafunc):
    import django

    django.setup()
    if "panel" in metafunc.fixturenames:
        m = []
        ids = []
        for panel in site.console_panels:
            m.append(pytest.param(panel, marks=[pytest.mark.admin]))
            ids.append(panel["label"])
        metafunc.parametrize("panel", m, ids=ids)


@pytest.mark.admin
def test_panel(panel, django_app, admin_user):
    url = reverse(f"admin:{panel['name']}")
    res = django_app.get(url, user=admin_user)
    assert res.status_code == 200


def test_panel_email(app, admin_user):
    url = reverse("admin:email")
    res = app.get(url, user=admin_user)
    res = res.forms[1].submit()
    assert res.status_code == 200
