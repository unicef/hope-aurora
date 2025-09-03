import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse


@pytest.fixture
def app(db, django_app_factory):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app


def test_editor_info(app):
    url = reverse("editor_info")
    res = app.get(url, user=AnonymousUser())
    assert res.status_code == 302


def test_smartjavascriptcatalog(app):
    url = reverse("javascript-catalog", args=["it-it"])
    res = app.get(url, user=AnonymousUser())
    assert res.status_code == 200
