"""Render all times in the clinic's local timezone"""

from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone


class ClinicTimezoneMiddleware:
    """Activate the clinic timezone so templates show local times, not UTC"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        timezone.activate(ZoneInfo(settings.CLINIC_TIMEZONE))
        return self.get_response(request)
