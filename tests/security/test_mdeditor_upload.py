import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_mdeditor_upload_requires_staff(client):
    response = client.post(reverse("uploads"))
    assert response.status_code == 302


@pytest.mark.django_db
def test_mdeditor_upload_allows_staff(client, admin_user):
    client.force_login(admin_user)
    response = client.post(reverse("uploads"))
    assert response.status_code == 200
    assert response.json()["success"] == 0
