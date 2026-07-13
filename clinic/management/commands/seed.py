"""Seed idempotent demo data: five doctors with varied hours and a demo patient"""

from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from clinic.models import Doctor, Patient, WorkingHours

# (name, weekdays, start, end)
DOCTORS = [
    ("Dr. Achieng", range(5), time(9, 0), time(17, 0)),
    ("Dr. Barasa", range(5), time(8, 0), time(14, 0)),
    ("Dr. Chebet", (0, 1, 2, 3), time(10, 0), time(18, 0)),
    ("Dr. Diallo", range(5), time(9, 0), time(17, 0)),
    ("Dr. Mutuiri", (0, 2, 4), time(9, 0), time(13, 0)),
]


class Command(BaseCommand):
    help = "Create idempotent demo data for local dev and a fresh deploy"

    def handle(self, *args, **options):
        for name, weekdays, start, end in DOCTORS:
            doctor, _ = Doctor.objects.get_or_create(name=name)
            for weekday in weekdays:
                WorkingHours.objects.get_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    defaults={"start_time": start, "end_time": end},
                )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="Addy", defaults={"role": "patient"}
        )
        if created:
            user.set_password("addy12345")
            user.save(update_fields=["password"])
        Patient.objects.get_or_create(user=user, defaults={"name": "Addy Makau"})

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DOCTORS)} doctors and demo patient"))
