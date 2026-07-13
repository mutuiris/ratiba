import pytest
from django.db.utils import IntegrityError
from django.utils import timezone

from clinic.models import Appointment, Doctor, Patient


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
