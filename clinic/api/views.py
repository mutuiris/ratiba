"""DRF views mapping HTTP to the booking services"""

from datetime import date

from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from clinic.api.permissions import check_appointment, check_patient
from clinic.api.serializers import (
    AppointmentSerializer,
    BookRequestSerializer,
    CancelRequestSerializer,
    RescheduleRequestSerializer,
)
from clinic.models import Appointment, Doctor
from clinic.services import booking
from clinic.services.appointments import upcoming_for_patient
from clinic.services.availability import get_availability
from clinic.services.exceptions import BookingError


@api_view(["POST"])
def create_appointment(request):
    """Book a slot for a patient"""
    data = BookRequestSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    check_patient(request, data.validated_data["patient"])
    try:
        appt = booking.book(
            data.validated_data["doctor"],
            data.validated_data["patient"],
            data.validated_data["start_at"],
            idempotency_key=request.headers.get("Idempotency-Key"),
        )
    except BookingError as exc:
        return Response({"detail": exc.message}, status=exc.http_status)
    return Response(AppointmentSerializer(appt).data, status=201)


@api_view(["GET"])
def doctor_availability(request, doctor_id):
    """List a doctor's free 30-minute slots for a date"""
    get_object_or_404(Doctor, pk=doctor_id)
    raw = request.query_params.get("date")
    if not raw:
        return Response({"detail": "A date query parameter is required"}, status=400)
    try:
        day = date.fromisoformat(raw)
    except ValueError:
        return Response({"detail": "date must be in YYYY-MM-DD format"}, status=400)
    return Response({"date": raw, "slots": get_availability(doctor_id, day)})


@api_view(["PATCH"])
def cancel_appointment(request, pk):
    """Cancel an appointment and free its slot"""
    data = CancelRequestSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    check_appointment(request, get_object_or_404(Appointment, pk=pk))
    try:
        appt = booking.cancel(pk, data.validated_data["reason"])
    except BookingError as exc:
        return Response({"detail": exc.message}, status=exc.http_status)
    return Response(AppointmentSerializer(appt).data)


@api_view(["PATCH"])
def reschedule_appointment(request, pk):
    """Move an appointment to a new validated slot"""
    data = RescheduleRequestSerializer(data=request.data)
    data.is_valid(raise_exception=True)
    check_appointment(request, get_object_or_404(Appointment, pk=pk))
    try:
        appt = booking.reschedule(
            pk,
            data.validated_data["start_at"],
            new_doctor_id=data.validated_data.get("doctor"),
        )
    except BookingError as exc:
        return Response({"detail": exc.message}, status=exc.http_status)
    return Response(AppointmentSerializer(appt).data)


@api_view(["GET"])
def patient_appointments(request, pk):
    """List a patient's upcoming appointments"""
    check_patient(request, pk)
    appointments = upcoming_for_patient(pk)
    return Response(AppointmentSerializer(appointments, many=True).data)
