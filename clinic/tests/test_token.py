import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
def test_obtain_token_and_authenticate(doctor):
    User.objects.create_user("carol", password="secret", role="staff")
    client = APIClient()

    token = client.post("/api/token", {"username": "carol", "password": "secret"}, format="json")
    assert token.status_code == 200
    assert "access" in token.data

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.data['access']}")
    response = client.get(f"/api/doctors/{doctor.id}/availability?date=2026-07-15")
    assert response.status_code == 200


@pytest.mark.django_db
def test_missing_token_is_rejected(doctor):
    response = APIClient().get(f"/api/doctors/{doctor.id}/availability?date=2026-07-15")
    assert response.status_code in (401, 403)
