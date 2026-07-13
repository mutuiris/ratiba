from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

UTC = ZoneInfo("UTC")


@pytest.fixture
def frozen_now(monkeypatch):
    fixed = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)  # 03:00 Nairobi, before the workday
    monkeypatch.setattr("django.utils.timezone.now", lambda: fixed)
    return fixed


@pytest.fixture
def auth_client(db):
    user = get_user_model().objects.create_user("staff1", password="x", role="staff")
    api = APIClient()
    api.force_authenticate(user)
    return api


@pytest.mark.django_db
def test_book_returns_201(auth_client, doctor, patient, frozen_now):
    body = {"doctor": doctor.id, "patient": patient.id, "start_at": "2026-07-15T06:00:00Z"}
    response = auth_client.post("/api/appointments", body, format="json")
    assert response.status_code == 201
    assert response.data["status"] == "booked"


@pytest.mark.django_db
def test_book_taken_returns_409(auth_client, doctor, patient, frozen_now):
    body = {"doctor": doctor.id, "patient": patient.id, "start_at": "2026-07-15T06:00:00Z"}
    auth_client.post("/api/appointments", body, format="json")
    response = auth_client.post("/api/appointments", body, format="json")
    assert response.status_code == 409
    assert "taken" in response.data["detail"].lower()


@pytest.mark.django_db
def test_book_bad_datetime_returns_400(auth_client, doctor, patient, frozen_now):
    body = {"doctor": doctor.id, "patient": patient.id, "start_at": "not-a-date"}
    response = auth_client.post("/api/appointments", body, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_availability_returns_16_slots(auth_client, doctor, frozen_now):
    response = auth_client.get(f"/api/doctors/{doctor.id}/availability?date=2026-07-15")
    assert response.status_code == 200
    assert len(response.data["slots"]) == 16


@pytest.mark.django_db
def test_availability_missing_date_returns_400(auth_client, doctor, frozen_now):
    response = auth_client.get(f"/api/doctors/{doctor.id}/availability")
    assert response.status_code == 400


@pytest.mark.django_db
def test_reschedule_then_cancel_flow(auth_client, doctor, patient, frozen_now):
    body = {"doctor": doctor.id, "patient": patient.id, "start_at": "2026-07-15T06:00:00Z"}
    appt_id = auth_client.post("/api/appointments", body, format="json").data["id"]

    moved = auth_client.patch(
        f"/api/appointments/{appt_id}/reschedule",
        {"start_at": "2026-07-15T07:00:00Z"},
        format="json",
    )
    assert moved.status_code == 200

    cancelled = auth_client.patch(
        f"/api/appointments/{appt_id}/cancel", {"reason": "sick"}, format="json"
    )
    assert cancelled.status_code == 200
    assert cancelled.data["status"] == "cancelled"


@pytest.mark.django_db
def test_unauthenticated_is_rejected(doctor, patient):
    response = APIClient().post("/api/appointments", {}, format="json")
    assert response.status_code in (401, 403)
