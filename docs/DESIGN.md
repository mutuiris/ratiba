# System Design

## The Problem

A small clinic with 5 doctors needs an online appointment booking system. Each doctor has set working hours and works in 30-minute slots. Patients browse availability, book a slot (which becomes unavailable to others), and can cancel or reschedule.

## Models

```
User (AbstractUser)
  role: patient | staff

Patient
  user: OneToOne -> User (nullable)
  name, phone

Doctor
  name

WorkingHours
  doctor: FK -> Doctor
  weekday: 0-6 (Mon-Sun)
  start_time, end_time (local clinic time)
  UNIQUE(doctor, weekday)

TimeOff
  doctor: FK -> Doctor
  start_at, end_at (UTC)
  reason

Appointment
  doctor: FK -> Doctor
  patient: FK -> Patient
  start_at, end_at (UTC)
  status: booked | cancelled
  cancel_reason, cancelled_at
  idempotency_key (unique, nullable)
  UNIQUE(doctor, start_at) WHERE status='booked'
```

## Key Design Decisions

### 1. Computed Slots, Not Stored Slots

Slots are not rows in the database. Availability is computed on the fly:

```
WorkingHours -> generate 30-min grid -> subtract booked appointments -> subtract time-offs -> subtract too-soon slots
```

**Why**: Single source of truth. No synchronisation problems between a `Slot` table and `WorkingHours`. Schedule changes take effect immediately.

**Trade-off**: If working hours shrink, existing appointments outside the new hours are not automatically invalidated. At scale, a conflict detection job would flag orphans.

### 2. UTC Storage, Local Display

All `DateTimeField` values store UTC. The clinic operates in `Africa/Nairobi` (UTC+3). Conversion happens at:

- **Input**: `slot_starts()` combines local working hours with the clinic timezone, converts to UTC.
- **Output**: `ClinicTimezoneMiddleware` activates the timezone for templates. API returns UTC (clients convert).

**Why**: Comparison correctness. The unique constraint `(doctor, start_at) WHERE booked` compares absolute moments. Two patients in different timezones submitting "14:00" must be compared against the same instant.

### 3. Partial Unique Index for Double-Booking Prevention

```python
UniqueConstraint(
    fields=["doctor", "start_at"],
    condition=Q(status="booked"),
    name="one_active_booking_per_slot",
)
```

The database itself prevents double-booking. Even under concurrent requests, only one `INSERT` with `status='booked'` can succeed for a given `(doctor, start_at)`. The second gets an `IntegrityError` caught as `SlotTaken`.

**Why**: Application  level checks have race windows.

### 4. Reschedule as Atomic Update in Place

Rescheduling updates the existing `Appointment` row rather than cancelling and re-booking:

```python
appt.start_at = new_start
appt.end_at = new_start + SLOT
appt.save(update_fields=[...])  # inside transaction.atomic()
```

**Why**: If we cancel, then book, there is a window where another patient could take the original slot, leaving the rescheduling patient with nothing. Update-in-place means the row never enters a "free" state. If the new slot is taken (`IntegrityError`), `refresh_from_db()` restores the original - the patient always has an appointment.

### 5. Compare-and-Set Cancellation

```python
updated = Appointment.objects.filter(id=id, status="booked").update(status="cancelled", ...)
if updated == 0:
    raise AlreadyCancelled()
```

**Why**: The check and write happen in one SQL statement. Two concurrent cancel requests cannot both succeed - one gets `updated=1`, the other gets `updated=0`.

### 6. Idempotency Keys

The booking endpoint accepts an `Idempotency-Key` header. If the same key appears twice, the second request returns the already created appointment instead of booking a new one.

**Why**: Network failures, impatient users, or frontend retry logic should not create duplicate appointments.

## Assumptions and Decisions

**Slot representation:**  I chose to derive them from working hours rules rather than materialising rows, because a single source of truth eliminates drift between schedule config and bookable inventory.

**Initiation of the Booking:** Patients book their own appointments, and staff to book via the API with an ownership check.

**When doctor changes the schedule:**  Leave existing appointments untouched and let admin handle conflicts manually. The alternative (cascading cancellation) risks data loss and surprise notifications to patients who already confirmed.

**Booking session from now** By setting a 1-hour lead time because it gives the doctor preparation time and avoids the edge case of booking a slot that starts in 2 minutes.

**Can a patient hold more than one appointment on the same day?** Yes, by adding a per-day cap later is a single queryset filter in the service layer.

**Time stored and display** By storing all instants as UTC and display in the clinic's local timezone (`Africa/Nairobi`). This ensures the unique constraint compares absolute moments regardless of where the request originates.

## Concurrency Model

- **Booking**: `transaction.atomic()` + unique constraint = exactly one winner
- **Cancellation**: atomic compare-and-set via `.filter().update()`
- **Rescheduling**: `transaction.atomic()` + update-in-place = no slot loss on failure
- **Availability reads**: No locking — eventual consistency is acceptable for display (validation at book time catches stale reads)
