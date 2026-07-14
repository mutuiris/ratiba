from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from clinic.services import exceptions as ex
from clinic.services.booking import book

UTC = ZoneInfo("UTC")


def slot(hour, minute=0):
    # 09:00 Nairobi == 06:00 UTC
    return datetime(2026, 7, 15, hour, minute, tzinfo=UTC)


@pytest.mark.django_db
def test_book_success(doctor, patient):
    appt = book(doctor.id, patient.id, slot(6), now=slot(0))
    assert appt.status == "booked"
    assert appt.end_at == slot(6, 30)


@pytest.mark.django_db
def test_book_outside_hours(doctor, patient):
    with pytest.raises(ex.OutsideHours, match="outside"):
        book(doctor.id, patient.id, slot(3), now=slot(0))


@pytest.mark.django_db
def test_book_not_working_that_day(doctor, patient):
    saturday = datetime(2026, 7, 18, 6, 0, tzinfo=UTC)
    with pytest.raises(ex.OutsideHours, match="not working that day"):
        book(doctor.id, patient.id, saturday, now=slot(0))


@pytest.mark.django_db
def test_book_in_past(doctor, patient):
    with pytest.raises(ex.InPast, match="past"):
        book(doctor.id, patient.id, slot(6), now=slot(8))


@pytest.mark.django_db
def test_book_too_soon(doctor, patient):
    with pytest.raises(ex.TooSoon, match="within 1 hour"):
        book(doctor.id, patient.id, slot(6), now=slot(5, 30))


@pytest.mark.django_db
def test_book_off_grid_rejected(doctor, patient):
    with pytest.raises(ex.OffGrid, match="30-minute"):
        book(doctor.id, patient.id, slot(6, 7), now=slot(0))


@pytest.mark.django_db
def test_book_unknown_patient_rejected(doctor):
    with pytest.raises(ex.UnknownPatient, match="Unknown patient"):
        book(doctor.id, 999999, slot(6), now=slot(0))


@pytest.mark.django_db
def test_book_taken(doctor, patient):
    book(doctor.id, patient.id, slot(6), now=slot(0))
    with pytest.raises(ex.SlotTaken, match="already taken"):
        book(doctor.id, patient.id, slot(6), now=slot(0))


@pytest.mark.django_db
def test_idempotent_repeat_returns_same(doctor, patient):
    a = book(doctor.id, patient.id, slot(6), now=slot(0), idempotency_key="k1")
    b = book(doctor.id, patient.id, slot(7), now=slot(0), idempotency_key="k1")
    assert a.id == b.id
