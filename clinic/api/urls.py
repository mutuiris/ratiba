"""URL routes for the appointment API"""

from django.urls import path

from clinic.api import views

urlpatterns = [
    path("appointments", views.create_appointment, name="create-appointment"),
    path("appointments/<int:pk>/cancel", views.cancel_appointment, name="cancel-appointment"),
    path(
        "appointments/<int:pk>/reschedule",
        views.reschedule_appointment,
        name="reschedule-appointment",
    ),
    path(
        "doctors/<int:doctor_id>/availability",
        views.doctor_availability,
        name="doctor-availability",
    ),
    path(
        "patients/<int:pk>/appointments",
        views.patient_appointments,
        name="patient-appointments",
    ),
]
