"""URL routes for the patient web UI"""

from django.urls import path

from clinic.web import views

urlpatterns = [
    path("", views.doctors, name="web-doctors"),
    path("doctors/<int:doctor_id>/availability", views.availability, name="web-availability"),
    path("doctors/<int:doctor_id>/book", views.book, name="web-book"),
    path("appointments", views.appointments, name="web-appointments"),
    path("appointments/<int:pk>/cancel", views.cancel, name="web-cancel"),
    path("appointments/<int:pk>/reschedule", views.reschedule, name="web-reschedule"),
]
