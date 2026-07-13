from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from clinic.models import Patient
from clinic.services.booking import book

UTC = ZoneInfo("UTC")
User = get_user_model()


@pytest.fixture
def frozen_now(monkeypatch):
    fixed = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    return fixed


@pytest.fixture
def patient_client(db):
    user = User.objects.create_user("alice", password="secret", role="patient")
    Patient.objects.create(user=user, name="Alice")
    client = Client()
    client.force_login(user)
    return client, user


@pytest.mark.django_db
def test_login_page_renders(client):
    assert client.get("/login/").status_code == 200


@pytest.mark.django_db
def test_home_requires_login(client):
    response = client.get("/")
    assert response.status_code == 302
    assert "/login/" in response.url


@pytest.mark.django_db
def test_doctors_page_lists_doctor(patient_client, doctor):
    client, _ = patient_client
    response = client.get("/")
    assert response.status_code == 200
    assert doctor.name in response.content.decode()


@pytest.mark.django_db
def test_book_via_web_creates_and_redirects(patient_client, doctor, frozen_now):
    client, _ = patient_client
    response = client.post(f"/doctors/{doctor.id}/book", {"start_at": "2026-07-15T06:00:00+00:00"})
    assert response.status_code == 302
    assert response.url == "/appointments"


@pytest.mark.django_db
def test_appointments_page_lists_booking(patient_client, doctor, frozen_now):
    client, user = patient_client
    book(doctor.id, user.patient.id, datetime(2026, 7, 15, 6, 0, tzinfo=UTC), now=frozen_now)
    response = client.get("/appointments")
    assert response.status_code == 200
    assert doctor.name in response.content.decode()
