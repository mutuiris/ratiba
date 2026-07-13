import pytest
from django.core.management import call_command

from clinic.models import Doctor, WorkingHours


@pytest.mark.django_db
def test_seed_is_idempotent():
    call_command("seed")
    call_command("seed")
    assert Doctor.objects.count() == 5
    assert WorkingHours.objects.count() == 25  # 5 doctors x 5 weekdays
