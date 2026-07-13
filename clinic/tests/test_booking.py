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
    with pytest.raises(ex.OutsideHours):
        book(doctor.id, patient.id, slot(3), now=slot(0))  # 06:00 Nairobi, before 09:00


@pytest.mark.django_db
def test_book_in_past(doctor, patient):
    with pytest.raises(ex.InPast):
        book(doctor.id, patient.id, slot(6), now=slot(8))


@pytest.mark.django_db
def test_book_off_grid_rejected(doctor, patient):
    with pytest.raises(ex.OffGrid):
        book(doctor.id, patient.id, slot(6, 7), now=slot(0))  # 09:07 Nairobi, not on the grid


@pytest.mark.django_db
def test_book_unknown_patient_rejected(doctor):
    with pytest.raises(ex.UnknownPatient):
        book(doctor.id, 999999, slot(6), now=slot(0))


@pytest.mark.django_db
def test_book_taken(doctor, patient):
    book(doctor.id, patient.id, slot(6), now=slot(0))
    with pytest.raises(ex.SlotTaken):
        book(doctor.id, patient.id, slot(6), now=slot(0))


@pytest.mark.django_db
def test_idempotent_repeat_returns_same(doctor, patient):
    a = book(doctor.id, patient.id, slot(6), now=slot(0), idempotency_key="k1")
    b = book(doctor.id, patient.id, slot(7), now=slot(0), idempotency_key="k1")
    assert a.id == b.id  # same key returns the original, second slot ignored
