import pytest
from django.contrib.sites.models import Site
from testutils.factories import FlatPageFactory


@pytest.fixture
def page(db):
    pg = FlatPageFactory(url="/url/")
    pg.sites.add(Site.objects.get_current())
    return pg


@pytest.fixture
def app(django_app_factory):
    from testutils.factories import SuperUserFactory

    admin_user = SuperUserFactory(username="superuser")
    django_app = django_app_factory(csrf_checks=False)
    django_app.set_user(admin_user)
    django_app._user = admin_user
    return django_app
