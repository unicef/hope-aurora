import pytest
from django.contrib.auth.models import Group
from django.urls import reverse
from pyquery import PyQuery

from aurora.core.models import Organization

# Note in case cassettes need to be refreshed
#  See. https://github.com/getsentry/responses?tab=readme-ov-file#record-responses-to-files


@pytest.fixture
def app(django_app_factory, db):
    from testutils.factories import GroupFactory, OrganizationFactory, SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    GroupFactory()
    OrganizationFactory()
    return django_app


@pytest.mark.record(False)
def test_sync_multi(app, file_mocked_responses):
    email = "sax@unicef.org"
    res = reverse("admin:security_user_changelist")
    res = app.get(res)
    res = res.click("Load Ad Users")
    res.forms["load_users"]["emails"] = f"{email} uknknown@unicef.org"
    res.forms["load_users"]["role"] = Group.objects.first().id
    res.forms["load_users"]["organization"] = Organization.objects.first().id
    res = res.forms["load_users"].submit()
    imported = PyQuery(res.text)("#imported div").text()
    assert imported == email
    missing = PyQuery(res.text)("#missing div").text()
    assert missing == "uknknown@unicef.org"
