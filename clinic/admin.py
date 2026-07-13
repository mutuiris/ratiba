"""Admin configuration for the clinic domain models"""

from django.contrib import admin, messages

from clinic.models import Appointment, Doctor, Patient, TimeOff, WorkingHours


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "phone")
    search_fields = ("name", "phone")


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ("doctor", "weekday", "start_time", "end_time")
    list_filter = ("doctor", "weekday")


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ("doctor", "start_at", "end_at", "reason", "affected_bookings")
    list_filter = ("doctor",)
    date_hierarchy = "start_at"

    @admin.display(description="Affected bookings")
    def affected_bookings(self, obj):
        count = Appointment.objects.filter(
            doctor=obj.doctor,
            status="booked",
            start_at__lt=obj.end_at,
            end_at__gt=obj.start_at,
        ).count()
        return count or "—"

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        conflicts = Appointment.objects.filter(
            doctor=obj.doctor,
            status="booked",
            start_at__lt=obj.end_at,
            end_at__gt=obj.start_at,
        ).select_related("patient")
        if conflicts.exists():
            names = ", ".join(f"{a.patient.name} ({a.start_at:%H:%M})" for a in conflicts)
            messages.warning(
                request,
                f"⚠ {conflicts.count()} booked appointment(s) overlap this time-off: {names}",
            )


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("patient", "doctor", "start_at", "end_at", "status")
    list_filter = ("status", "doctor")
    date_hierarchy = "start_at"
    search_fields = ("patient__name", "doctor__name")
