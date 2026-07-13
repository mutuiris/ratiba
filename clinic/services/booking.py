"""Booking operations: create, cancel, and reschedule appointments"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from clinic.models import Appointment, Patient, WorkingHours
from clinic.services import exceptions as ex
from clinic.services.slots import SLOT

# process local idempotency cache, pushed to a DB table if multiple workers run
_SEEN_KEYS: dict[str, int] = {}


def _validate_slot(doctor_id: int, start_at: datetime, now: datetime) -> None:
    """Raise a BookingError if start_at is in the past, too soon, or outside working hours"""
    if start_at < now:
        raise ex.InPast()
    if start_at < now + timedelta(minutes=settings.BOOKING_LEAD_MINUTES):
        raise ex.TooSoon()

    tz = ZoneInfo(settings.CLINIC_TIMEZONE)
    local = start_at.astimezone(tz)
    try:
        hours = WorkingHours.objects.get(doctor_id=doctor_id, weekday=local.date().weekday())
    except WorkingHours.DoesNotExist:
        raise ex.OutsideHours("Doctor is not working that day") from None

    slot_end_local = (start_at + SLOT).astimezone(tz).time()
    if not (hours.start_time <= local.time() and slot_end_local <= hours.end_time):
        raise ex.OutsideHours("Slot is outside the doctor's working hours")

    offset = (local.hour - hours.start_time.hour) * 60 + (local.minute - hours.start_time.minute)
    if local.second or local.microsecond or offset % settings.SLOT_MINUTES != 0:
        raise ex.OffGrid()


def book(
    doctor_id: int,
    patient_id: int,
    start_at: datetime,
    now: datetime | None = None,
    idempotency_key: str | None = None,
) -> Appointment:
    """Create a booked appointment for a validated slot, raising BookingError on failure"""
    now = now or timezone.now()
    if idempotency_key and idempotency_key in _SEEN_KEYS:
        return Appointment.objects.get(pk=_SEEN_KEYS[idempotency_key])

    if not Patient.objects.filter(pk=patient_id).exists():
        raise ex.UnknownPatient()
    _validate_slot(doctor_id, start_at, now)
    try:
        with transaction.atomic():
            appt = Appointment.objects.create(
                doctor_id=doctor_id,
                patient_id=patient_id,
                start_at=start_at,
                end_at=start_at + SLOT,
                status="booked",
            )
    except IntegrityError as exc:
        raise ex.SlotTaken() from exc

    if idempotency_key:
        _SEEN_KEYS[idempotency_key] = appt.pk
    return appt


def cancel(appointment_id: int, reason: str) -> Appointment:
    """Cancel a booked appointment, raising AlreadyCancelled if it was not booked"""
    updated = Appointment.objects.filter(id=appointment_id, status="booked").update(
        status="cancelled", cancel_reason=reason, cancelled_at=timezone.now()
    )
    if updated == 0:  # compare-and-set, 0 rows means it was not booked on arrival
        raise ex.AlreadyCancelled()
    return Appointment.objects.get(pk=appointment_id)


def reschedule(
    appointment_id: int, new_start: datetime, now: datetime | None = None
) -> Appointment:
    """Move a booked appointment to a new validated slot as one atomic update"""
    now = now or timezone.now()
    appt = Appointment.objects.get(pk=appointment_id)
    if appt.status != "booked":
        raise ex.Cancelled()

    _validate_slot(appt.doctor_id, new_start, now)
    appt.start_at = new_start
    appt.end_at = new_start + SLOT
    try:
        with transaction.atomic():
            appt.save(update_fields=["start_at", "end_at"])
    except IntegrityError as exc:
        appt.refresh_from_db()  # new slot taken, original row is untouched
        raise ex.SlotTaken() from exc
    return appt
