from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from clinic.services.appointments import upcoming_for_patient
from clinic.services.booking import book, cancel

UTC = ZoneInfo("UTC")


def slot(hour):
    return datetime(2026, 7, 15, hour, 0, tzinfo=UTC)


@pytest.mark.django_db
def test_upcoming_sorted_ascending(doctor, patient):
    book(doctor.id, patient.id, slot(8), now=slot(0))
    book(doctor.id, patient.id, slot(6), now=slot(0))
    starts = [a.start_at for a in upcoming_for_patient(patient.id, now=slot(0))]
    assert starts == sorted(starts)
    assert len(starts) == 2


@pytest.mark.django_db
def test_excludes_past_and_cancelled(doctor, patient):
    book(doctor.id, patient.id, slot(6), now=slot(0))  # will be in the past
    book(doctor.id, patient.id, slot(8), now=slot(0))
    cancelled = book(doctor.id, patient.id, slot(9), now=slot(0))
    cancel(cancelled.id, "x")
    starts = [a.start_at for a in upcoming_for_patient(patient.id, now=slot(7))]
    assert starts == [slot(8)]  # 06:00 is past, 09:00 is cancelled
