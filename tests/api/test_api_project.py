from typing import TYPE_CHECKING

import pytest
from rest_framework.test import APIClient
from testutils.factories import TokenProxyFactory, RegistrationFactory

if TYPE_CHECKING:
    from aurora.registration.models import Project


@pytest.fixture
def project(simple_form) -> "Project":
    from testutils.factories import ProjectFactory

    prj = ProjectFactory()
    RegistrationFactory(project=prj)
    return prj


@pytest.fixture
def client(admin_user):
    client = APIClient()
    token = TokenProxyFactory(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
    return client


def test_project_list(project: "Project", client):
    res = client.get("/api/project/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_project_detail(project: "Project", client):
    res = client.get(f"/api/project/{project.pk}/", format="json")
    assert res.status_code == 200
    assert res.json()


def test_project_registrations(project: "Project", client):
    res = client.get(f"/api/project/{project.pk}/registrations/", format="json")
    assert res.status_code == 200
    assert res.json()
