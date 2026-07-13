"""Request and response serializers for the appointment API"""

from rest_framework import serializers

from clinic.models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    """Response shape for an appointment"""

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor",
            "patient",
            "start_at",
            "end_at",
            "status",
            "cancel_reason",
            "created_at",
            "cancelled_at",
        ]
        read_only_fields = ["end_at", "status", "created_at", "cancelled_at"]


class BookRequestSerializer(serializers.Serializer):
    """Input for POST /appointments"""

    doctor = serializers.IntegerField()
    patient = serializers.IntegerField()
    start_at = serializers.DateTimeField()


class RescheduleRequestSerializer(serializers.Serializer):
    """Input for PATCH /appointments/{id}/reschedule"""

    start_at = serializers.DateTimeField()
    doctor = serializers.IntegerField(required=False)


class CancelRequestSerializer(serializers.Serializer):
    """Input for PATCH /appointments/{id}/cancel"""

    reason = serializers.CharField(max_length=200)
