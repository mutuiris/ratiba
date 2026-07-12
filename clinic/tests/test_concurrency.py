from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, time
from zoneinfo import ZoneInfo

import pytest
from django.db import connections

from clinic.models import Doctor, Patient, WorkingHours
from clinic.services import exceptions as ex
from clinic.services.booking import book, cancel

UTC = ZoneInfo("UTC")


def slot(hour):
    return datetime(2026, 7, 15, hour, 0, tzinfo=UTC)  # Wednesday


def _make_clinic():
    doc = Doctor.objects.create(name="Otieno")
    WorkingHours.objects.create(doctor=doc, weekday=2, start_time=time(9), end_time=time(17))
    pat = Patient.objects.create(name="A")
    return doc, pat


def _run(fn):
    try:
        fn()
        return "ok"
    except ex.BookingError as exc:
        return type(exc).__name__
    finally:
        connections.close_all()  # each thread uses its own connection


@pytest.mark.django_db(transaction=True)
def test_two_bookings_same_slot_one_wins():
    doc, pat = _make_clinic()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(_run, lambda: book(doc.id, pat.id, slot(6), now=slot(0)))
            for _ in range(2)
        ]
        results = [f.result() for f in futures]
    assert sorted(results) == ["SlotTaken", "ok"]  # exactly one wins


@pytest.mark.django_db(transaction=True)
def test_double_cancel_one_wins():
    doc, pat = _make_clinic()
    appt = book(doc.id, pat.id, slot(6), now=slot(0))
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run, lambda: cancel(appt.id, "race")) for _ in range(2)]
        results = [f.result() for f in futures]
    assert sorted(results) == ["AlreadyCancelled", "ok"]  # one 200, one 409
