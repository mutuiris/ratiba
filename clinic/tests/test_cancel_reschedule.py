from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from clinic.services import exceptions as ex
from clinic.services.booking import book, cancel, reschedule

UTC = ZoneInfo("UTC")


def slot(hour, minute=0):
    return datetime(2026, 7, 15, hour, minute, tzinfo=UTC)


@pytest.mark.django_db
def test_cancel_frees_slot(doctor, patient):
    appt = book(doctor.id, patient.id, slot(6), now=slot(0))
    cancel(appt.id, "patient sick")
    rebooked = book(doctor.id, patient.id, slot(6), now=slot(0))
    assert rebooked.status == "booked"


@pytest.mark.django_db
def test_double_cancel_409(doctor, patient):
    appt = book(doctor.id, patient.id, slot(6), now=slot(0))
    cancel(appt.id, "once")
    with pytest.raises(ex.AlreadyCancelled):
        cancel(appt.id, "twice")


@pytest.mark.django_db
def test_reschedule_moves_and_frees_original(doctor, patient):
    appt = book(doctor.id, patient.id, slot(6), now=slot(0))
    reschedule(appt.id, slot(7), now=slot(0))
    appt.refresh_from_db()
    assert appt.start_at == slot(7)
    freed = book(doctor.id, patient.id, slot(6), now=slot(0))
    assert freed.status == "booked"


@pytest.mark.django_db
def test_reschedule_into_taken_keeps_original(doctor, patient):
    appt = book(doctor.id, patient.id, slot(6), now=slot(0))
    book(doctor.id, patient.id, slot(7), now=slot(0))  # 07:00 already held
    with pytest.raises(ex.SlotTaken):
        reschedule(appt.id, slot(7), now=slot(0))
    appt.refresh_from_db()
    assert appt.start_at == slot(6)
    assert appt.status == "booked"


@pytest.mark.django_db
def test_reschedule_cancelled_409(doctor, patient):
    appt = book(doctor.id, patient.id, slot(6), now=slot(0))
    cancel(appt.id, "x")
    with pytest.raises(ex.Cancelled):
        reschedule(appt.id, slot(7), now=slot(0))
