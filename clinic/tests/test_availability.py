from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from clinic.models import Appointment, TimeOff
from clinic.services.availability import get_availability

UTC = ZoneInfo("UTC")
WED = date(2026, 7, 15)  # a Wednesday
MIDNIGHT = datetime(2026, 7, 15, 0, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_full_day_has_16_slots(doctor):
    assert len(get_availability(doctor.id, WED, now=MIDNIGHT)) == 16


@pytest.mark.django_db
def test_booked_slot_removed(doctor, patient):
    slots = get_availability(doctor.id, WED, now=MIDNIGHT)
    Appointment.objects.create(
        doctor=doctor, patient=patient, start_at=slots[0], end_at=slots[0], status="booked"
    )
    after = get_availability(doctor.id, WED, now=MIDNIGHT)
    assert slots[0] not in after
    assert len(after) == 15


@pytest.mark.django_db
def test_timeoff_removes_overlapping_slots(doctor):
    # lunch 12:00-13:00 Nairobi == 09:00-10:00 UTC, covers two slots
    TimeOff.objects.create(
        doctor=doctor,
        start_at=datetime(2026, 7, 15, 9, 0, tzinfo=UTC),
        end_at=datetime(2026, 7, 15, 10, 0, tzinfo=UTC),
        reason="lunch",
    )
    assert len(get_availability(doctor.id, WED, now=MIDNIGHT)) == 14


@pytest.mark.django_db
def test_day_off_returns_empty(doctor):
    sunday = date(2026, 7, 19)
    assert get_availability(doctor.id, sunday, now=MIDNIGHT) == []


@pytest.mark.django_db
def test_lead_time_filters_near_now(doctor):
    # now = 10:00 Nairobi (07:00 UTC), +1h buffer blocks slots before 11:00 Nairobi (08:00 UTC)
    now = datetime(2026, 7, 15, 7, 0, tzinfo=UTC)
    slots = get_availability(doctor.id, WED, now=now)
    assert all(s >= datetime(2026, 7, 15, 8, 0, tzinfo=UTC) for s in slots)
