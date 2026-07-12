"""Server-rendered pages for patients"""

from datetime import date, datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

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
        {"doctors": Doctor.objects.all(), "today": date.today().isoformat()},
    )


@login_required
def availability(request, doctor_id):
    """Show a doctor's free slots for the chosen date"""
    doctor = get_object_or_404(Doctor, pk=doctor_id)
    day = date.fromisoformat(request.GET.get("date") or date.today().isoformat())
    return render(
        request,
        "clinic/availability.html",
        {
            "doctor": doctor,
            "day": day,
            "slots": get_availability(doctor_id, day),
            "reschedule_id": request.GET.get("reschedule"),
        },
    )


@login_required
def book(request, doctor_id):
    """Book the chosen slot for the logged in patient"""
    start_at = datetime.fromisoformat(request.POST["start_at"])
    try:
        booking.book(doctor_id, request.user.patient.id, start_at)
        messages.success(request, "Appointment booked")
    except BookingError as exc:
        messages.error(request, exc.message)
    return redirect("web-appointments")


@login_required
def reschedule(request, pk):
    """Move one of the patient's appointments to the chosen slot"""
    get_object_or_404(Appointment, pk=pk, patient__user=request.user)
    start_at = datetime.fromisoformat(request.POST["start_at"])
    try:
        booking.reschedule(pk, start_at)
        messages.success(request, "Appointment rescheduled")
    except BookingError as exc:
        messages.error(request, exc.message)
    return redirect("web-appointments")


@login_required
def appointments(request):
    """List the patient's upcoming appointments"""
    return render(
        request,
        "clinic/appointments.html",
        {"appointments": upcoming_for_patient(request.user.patient.id)},
    )


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
