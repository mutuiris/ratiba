"""Compute a doctor's free 30-minute slots for a given date"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from clinic.models import Appointment, TimeOff, WorkingHours
from clinic.services.slots import SLOT, slot_starts


def get_availability(doctor_id: int, day: date, now: datetime | None = None) -> list[datetime]:
    """Free UTC slot-starts for a doctor on day, ascending"""
    tz = ZoneInfo(settings.CLINIC_TIMEZONE)
    now = now or timezone.now()

    try:
        hours = WorkingHours.objects.get(doctor_id=doctor_id, weekday=day.weekday())
    except WorkingHours.DoesNotExist:
        return []  # doctor is off that day

    grid = slot_starts(day, hours.start_time, hours.end_time, tz)
    if not grid:
        return []

    day_start, day_end = grid[0], grid[-1] + SLOT

    # one query for booked slots, one for time-off, then set math
    booked = set(
        Appointment.objects.filter(
            doctor_id=doctor_id,
            status="booked",
            start_at__gte=day_start,
            start_at__lt=day_end,
        ).values_list("start_at", flat=True)
    )
    offs = list(
        TimeOff.objects.filter(
            doctor_id=doctor_id, start_at__lt=day_end, end_at__gt=day_start
        ).values_list("start_at", "end_at")
    )
    lead = now + timedelta(minutes=settings.BOOKING_LEAD_MINUTES)

    def is_free(slot: datetime) -> bool:
        if slot in booked or slot < lead:
            return False
        return not any(start < slot + SLOT and end > slot for start, end in offs)

    return [slot for slot in grid if is_free(slot)]
