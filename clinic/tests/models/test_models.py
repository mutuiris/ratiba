import pytest
from django.db.utils import IntegrityError
from django.utils import timezone

from clinic.models import Appointment, Doctor, Patient, TimeOff, WorkingHours


@pytest.mark.django_db
def test_partial_unique_blocks_second_active_booking():
    doctor = Doctor.objects.create(name="Otieno")
    patient = Patient.objects.create(name="A")
    start = timezone.now().replace(microsecond=0)
    Appointment.objects.create(
        doctor=doctor, patient=patient, start_at=start, end_at=start, status="booked"
    )
    with pytest.raises(IntegrityError):
        Appointment.objects.create(
            doctor=doctor, patient=patient, start_at=start, end_at=start, status="booked"
        )


@pytest.mark.django_db
def test_cancelled_row_does_not_block_rebooking():
    doctor = Doctor.objects.create(name="Otieno")
    patient = Patient.objects.create(name="A")
    start = timezone.now().replace(microsecond=0)
    Appointment.objects.create(
        doctor=doctor, patient=patient, start_at=start, end_at=start, status="cancelled"
    )
    Appointment.objects.create(
        doctor=doctor, patient=patient, start_at=start, end_at=start, status="booked"
    )
    assert Appointment.objects.filter(doctor=doctor, start_at=start).count() == 2


@pytest.mark.django_db
def test_doctor_str():
    assert str(Doctor.objects.create(name="Otieno")) == "Otieno"


@pytest.mark.django_db
def test_patient_str():
    assert str(Patient.objects.create(name="Alice")) == "Alice"


@pytest.mark.django_db
def test_working_hours_str():
    from datetime import time

    doc = Doctor.objects.create(name="Otieno")
    wh = WorkingHours.objects.create(doctor=doc, weekday=0, start_time=time(9), end_time=time(17))
    assert "Otieno" in str(wh)
    assert "09:00" in str(wh)


@pytest.mark.django_db
def test_timeoff_str():
    doc = Doctor.objects.create(name="Otieno")
    off = TimeOff.objects.create(
        doctor=doc,
        start_at=timezone.now(),
        end_at=timezone.now(),
        reason="break",
    )
    assert "Otieno" in str(off)


@pytest.mark.django_db
def test_appointment_str():
    doc = Doctor.objects.create(name="Otieno")
    pat = Patient.objects.create(name="Alice")
    now = timezone.now().replace(microsecond=0)
    appt = Appointment.objects.create(
        doctor=doc, patient=pat, start_at=now, end_at=now, status="booked"
    )
    s = str(appt)
    assert "Alice" in s
    assert "Otieno" in s
    assert "booked" in s
