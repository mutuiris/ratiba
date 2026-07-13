from datetime import time

import pytest

from clinic.models import Doctor, Patient, WorkingHours


@pytest.fixture
def doctor(db):
    """A doctor working Mon-Fri 09:00-17:00 local clinic time"""
    doc = Doctor.objects.create(name="Otieno")
    for weekday in range(5):
        WorkingHours.objects.create(
            doctor=doc, weekday=weekday, start_time=time(9), end_time=time(17)
        )
    return doc


@pytest.fixture
def patient(db):
    return Patient.objects.create(name="A")
