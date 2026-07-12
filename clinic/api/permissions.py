"""Object level authorization"""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from clinic.models import Patient


class IsOwnerOrStaff(BasePermission):
    """Staff act on any appointment, a patient only on their own"""

    message = "You can only act on your own appointments"

    def has_object_permission(self, request, view, obj):
        return request.user.role == "staff" or obj.patient.user_id == request.user.id


def check_appointment(request, appointment):
    """Reject the request unless the caller is staff or owns the appointment"""
    permission = IsOwnerOrStaff()
    if not permission.has_object_permission(request, None, appointment):
        raise PermissionDenied(permission.message)


def check_patient(request, patient_id):
    """Reject the request unless the caller is staff or is this patient"""
    if request.user.role == "staff":
        return
    if not Patient.objects.filter(id=patient_id, user_id=request.user.id).exists():
        raise PermissionDenied("You can only view your own appointments")
