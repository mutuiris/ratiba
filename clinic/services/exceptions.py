"""Domain errors for booking, mapped to an HTTP status"""


class BookingError(Exception):
    """Base booking error carrying a message and an HTTP status"""

    http_status = 400

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class OutsideHours(BookingError):
    pass


class InPast(BookingError):
    def __init__(self, message="Cannot book a slot in the past"):
        super().__init__(message)


class TooSoon(BookingError):
    def __init__(self, message="Cannot book within 1 hour of now"):
        super().__init__(message)


class OffGrid(BookingError):
    def __init__(self, message="Bookings must start on a 30-minute slot boundary"):
        super().__init__(message)


class UnknownPatient(BookingError):
    http_status = 404

    def __init__(self, message="Unknown patient"):
        super().__init__(message)


class SlotTaken(BookingError):
    http_status = 409

    def __init__(self, message="That slot is already taken"):
        super().__init__(message)


class AlreadyCancelled(BookingError):
    http_status = 409

    def __init__(self, message="Appointment is already cancelled"):
        super().__init__(message)


class Cancelled(BookingError):
    http_status = 409

    def __init__(self, message="Cannot reschedule a cancelled appointment"):
        super().__init__(message)
