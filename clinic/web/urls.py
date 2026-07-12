"""URL routes for the patient web UI"""

from django.contrib.auth import views as auth_views
from django.urls import path

from clinic.web import views

urlpatterns = [
    path("", views.doctors, name="web-doctors"),
    path("doctors/<int:doctor_id>/availability", views.availability, name="web-availability"),
    path("doctors/<int:doctor_id>/book", views.book, name="web-book"),
    path("appointments", views.appointments, name="web-appointments"),
    path("appointments/<int:pk>/cancel", views.cancel, name="web-cancel"),
    path("appointments/<int:pk>/reschedule", views.reschedule, name="web-reschedule"),
    path("login/", auth_views.LoginView.as_view(template_name="clinic/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
]
