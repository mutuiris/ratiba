from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from clinic.models import Patient
from clinic.services.booking import book

UTC = ZoneInfo("UTC")
User = get_user_model()


@pytest.fixture
def frozen_now(monkeypatch):
    fixed = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    return fixed


def make_patient(username):
    user = User.objects.create_user(username, password="x", role="patient")
    patient = Patient.objects.create(user=user, name=username)
    return user, patient


def client_for(user):
    api = APIClient()
    api.force_authenticate(user)
    return api


def book_for(doctor, patient, now):
    return book(doctor.id, patient.id, datetime(2026, 7, 15, 6, 0, tzinfo=UTC), now=now)


@pytest.mark.django_db
def test_patient_cannot_cancel_others_appointment(doctor, frozen_now):
    _, patient_a = make_patient("alice")
    user_b, _ = make_patient("bob")
    appt = book_for(doctor, patient_a, frozen_now)
    response = client_for(user_b).patch(
        f"/api/appointments/{appt.id}/cancel", {"reason": "nope"}, format="json"
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_patient_can_cancel_own_appointment(doctor, frozen_now):
    user_a, patient_a = make_patient("alice")
    appt = book_for(doctor, patient_a, frozen_now)
    response = client_for(user_a).patch(
        f"/api/appointments/{appt.id}/cancel", {"reason": "sick"}, format="json"
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_staff_can_cancel_any_appointment(doctor, frozen_now):
    _, patient_a = make_patient("alice")
    staff = User.objects.create_user("reception", password="x", role="staff")
    appt = book_for(doctor, patient_a, frozen_now)
    response = client_for(staff).patch(
        f"/api/appointments/{appt.id}/cancel", {"reason": "clinic closed"}, format="json"
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_patient_cannot_view_others_appointments(frozen_now):
    _, patient_a = make_patient("alice")
    user_b, _ = make_patient("bob")
    response = client_for(user_b).get(f"/api/patients/{patient_a.id}/appointments")
    assert response.status_code == 403
