"""Read queries over appointments"""

from datetime import datetime

from django.db.models import QuerySet
from django.utils import timezone

from clinic.models import Appointment


def upcoming_for_patient(patient_id: int, now: datetime | None = None) -> QuerySet[Appointment]:
    """Upcoming booked appointments for a patient, ascending by start_at"""
    now = now or timezone.now()
    return Appointment.objects.filter(
        patient_id=patient_id, status="booked", start_at__gte=now
    ).order_by("start_at")
