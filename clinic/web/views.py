"""Server-rendered pages for patients"""

from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from clinic.models import Appointment, Doctor
from clinic.services import booking
from clinic.services.appointments import upcoming_for_patient
from clinic.services.availability import get_availability
from clinic.services.exceptions import BookingError


@login_required
def doctors(request):
    """List doctors and let the patient pick a date"""
    return render(
        request,
        "clinic/doctors.html",
        {
            "doctors": Doctor.objects.all(),
            "today": date.today().isoformat(),
            "reschedule_id": request.GET.get("reschedule"),
        },
    )


@login_required
def availability(request, doctor_id):
    """Show a doctor's free slots for the chosen date"""
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    day = date.fromisoformat(request.GET.get("date") or date.today().isoformat())
    raw_slots = get_availability(doctor_id, day)
    fmt = [
        {"iso": s.isoformat(), "display": s.strftime("%H:%M"), "hour": s.hour} for s in raw_slots
    ]
    morning = [s for s in fmt if s["hour"] < 12]
    afternoon = [s for s in fmt if s["hour"] >= 12]
    return render(
        request,
        "clinic/availability.html",
        {
            "doctor": doctor,
            "day": day,
            "morning": morning,
            "afternoon": afternoon,
            "has_slots": bool(raw_slots),
            "reschedule_id": request.GET.get("reschedule"),
        },
    )


@require_POST
@login_required
def book(request, doctor_id):
    """Book the chosen slot for the logged in patient"""
    patient = getattr(request.user, "patient", None)
    if not patient:
        messages.error(request, "Staff accounts cannot book appointments")
        return redirect("web-doctors")
    raw = request.POST.get("start_at")
    if not raw:
        messages.error(request, "Missing slot time")
        return redirect("web-doctors")
    try:
        start_at = datetime.fromisoformat(raw)
        booking.book(doctor_id, patient.id, start_at)
        messages.success(request, "Appointment booked")
    except (ValueError, BookingError) as exc:
        messages.error(request, str(exc) if isinstance(exc, ValueError) else exc.message)
    return redirect("web-appointments")


@require_POST
@login_required
def reschedule(request, pk):
    """Move one of the patient's appointments to the chosen slot"""
    appt = get_object_or_404(Appointment, pk=pk, patient__user=request.user)
    raw = request.POST.get("start_at")
    if not raw:
        messages.error(request, "Missing slot time")
        return redirect("web-appointments")
    doctor_id = int(request.POST.get("doctor_id") or appt.doctor_id)  # type: ignore[attr-defined]
    try:
        start_at = datetime.fromisoformat(raw)
        booking.reschedule(pk, start_at, new_doctor_id=doctor_id)
        messages.success(request, "Appointment rescheduled")
    except (ValueError, BookingError) as exc:
        messages.error(request, str(exc) if isinstance(exc, ValueError) else exc.message)
    return redirect("web-appointments")


@login_required
def appointments(request):
    """List the patient's upcoming appointments"""
    patient = getattr(request.user, "patient", None)
    if not patient:
        return redirect("/admin/")
    return render(
        request,
        "clinic/appointments.html",
        {"appointments": upcoming_for_patient(patient.id)},
    )


@require_POST
@login_required
def cancel(request, pk):
    """Cancel one of the patient's appointments"""
    get_object_or_404(Appointment, pk=pk, patient__user=request.user)
    try:
        booking.cancel(pk, request.POST.get("reason", "cancelled by patient"))
        messages.success(request, "Appointment cancelled")
    except BookingError as exc:
        messages.error(request, exc.message)
    return redirect("web-appointments")
