from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from clinic.admin import TimeOffAdmin
from clinic.models import Appointment, TimeOff

UTC = ZoneInfo("UTC")
User = get_user_model()


@pytest.fixture
def admin_client(db):
    user = User.objects.create_superuser("admin", password="admin")
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_timeoff_save_warns_about_conflicts(admin_client, doctor, patient):
    Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        start_at=datetime(2026, 7, 15, 6, 0, tzinfo=UTC),
        end_at=datetime(2026, 7, 15, 6, 30, tzinfo=UTC),
        status="booked",
    )
    response = admin_client.post(
        "/admin/clinic/timeoff/add/",
        {
            "doctor": doctor.id,
            "start_at_0": "2026-07-15",
            "start_at_1": "05:00:00",
            "end_at_0": "2026-07-15",
            "end_at_1": "07:00:00",
            "reason": "emergency",
        },
    )
    assert response.status_code == 302
    assert TimeOff.objects.filter(doctor=doctor).exists()


@pytest.mark.django_db
def test_affected_bookings_counts_overlapping(doctor, patient):
    Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        start_at=datetime(2026, 7, 15, 6, 0, tzinfo=UTC),
        end_at=datetime(2026, 7, 15, 6, 30, tzinfo=UTC),
        status="booked",
    )
    off = TimeOff.objects.create(
        doctor=doctor,
        start_at=datetime(2026, 7, 15, 5, 0, tzinfo=UTC),
        end_at=datetime(2026, 7, 15, 7, 0, tzinfo=UTC),
        reason="meeting",
    )
    admin = TimeOffAdmin(TimeOff, None)
    assert admin.affected_bookings(off) == 1


@pytest.mark.django_db
def test_affected_bookings_none_returns_dash(doctor):
    off = TimeOff.objects.create(
        doctor=doctor,
        start_at=datetime(2026, 7, 15, 5, 0, tzinfo=UTC),
        end_at=datetime(2026, 7, 15, 7, 0, tzinfo=UTC),
        reason="day off",
    )
    admin = TimeOffAdmin(TimeOff, None)
    assert admin.affected_bookings(off) == "—"
