"""Domain models for the clinic: doctors, patients, schedules, and appointments"""

from django.conf import settings
from django.db import models


class Doctor(models.Model):
    """A clinician who sees patients in fixed 30-minute slots"""

    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name


class Patient(models.Model):
    """A person who books appointments with doctors"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="patient",
    )
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32, blank=True)

    def __str__(self):
        return self.name


class WorkingHours(models.Model):
    """A doctor's recurring availability for one weekday, in local clinic time"""

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="working_hours")
    weekday = models.PositiveSmallIntegerField() # 0=Monday, 6=Sunday
    start_time = models.TimeField() # local clinic time of day
    end_time = models.TimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "weekday"], name="one_rule_per_doctor_weekday"
            )
        ]

    def __str__(self):
        return f"{self.doctor} weekday {self.weekday} {self.start_time}-{self.end_time}"


class TimeOff(models.Model):
    """A one-off period a doctor is unavailable, such as a blocked day or a break."""

    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="time_off")
    start_at = models.DateTimeField()  # UTC
    end_at = models.DateTimeField()  # UTC
    reason = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.doctor} off {self.start_at}"


class Appointment(models.Model):
    """A booked 30-minute slot for one doctor and patient

    The partial unique index is the invariant: at most one active
    appointment may exist per doctor per slot-start. Cancelled rows are
    removed from the index
    """

    class Status(models.TextChoices):
        BOOKED = "booked"
        CANCELLED = "cancelled"

    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="appointments")
    start_at = models.DateTimeField()  # UTC
    end_at = models.DateTimeField()  # UTC
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.BOOKED)
    cancel_reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "start_at"],
                condition=models.Q(status="booked"),
                name="one_active_booking_per_slot",
            )
        ]
        indexes = [models.Index(fields=["doctor", "start_at"])]

    def __str__(self):
        return f"{self.patient} with {self.doctor} at {self.start_at} ({self.status})"
