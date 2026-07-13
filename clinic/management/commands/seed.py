"""Seed idempotent demo data: five doctors with weekday hours and a demo patient"""

from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from clinic.models import Doctor, Patient, WorkingHours

DOCTORS = ["Dr. Achieng", "Dr. Barasa", "Dr. Chebet", "Dr. Diallo", "Dr. Mutuiri"]
WEEKDAYS = range(5)  # Monday to Friday
OPEN, CLOSE = time(9, 0), time(17, 0)


class Command(BaseCommand):
    help = "Create idempotent demo data for local dev and a fresh deploy"

    def handle(self, *args, **options):
        for name in DOCTORS:
            doctor, _ = Doctor.objects.get_or_create(name=name)
            for weekday in WEEKDAYS:
                WorkingHours.objects.get_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    defaults={"start_time": OPEN, "end_time": CLOSE},
                )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username="Addy", defaults={"role": "patient"}
        )
        if created:
            user.set_password("addy12345")
            user.save(update_fields=["password"])
        Patient.objects.get_or_create(user=user, defaults={"name": "Addy Patient"})

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(DOCTORS)} doctors and the Addy patient"))
