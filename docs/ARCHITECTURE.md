# Architecture

## Project Structure

```
ratiba/
  config/             Django project settings, URLs, WSGI
    settings.py       config via django-environ
    urls.py           Root router: /api, /admin, /health, web views
  accounts/           Authentication app
    models.py         Custom User with role field
    views.py          Login/signup (server rendered)
    forms.py          Registration form
  clinic/             Core domain app
    models.py         Doctor, Patient, WorkingHours, TimeOff, Appointment
    services/         Business logic layer (no HTTP awareness)
      slots.py        30-minute grid math
      availability.py Compute free slots for a doctor+date
      booking.py      Book, cancel, reschedule operations
      appointments.py Read queries (upcoming appointments)
      exceptions.py   Domain errors with HTTP status codes
    api/              REST API (DRF)
      views.py        Thin HTTP handlers -> call services
      serializers.py  Request validation + response shaping
      permissions.py  Object-level auth (owner or staff)
    web/              Patient-facing UI (server-rendered)
      views.py        Thin HTTP handlers -> call services
      middleware.py   Timezone activation for templates
    templates/        HTML templates (doctors, availability, appointments)
    tests/            pytest test suite
    management/commands/seed.py  Idempotent demo data
  requirements/
    prod.txt          Runtime dependencies
    dev.txt           Includes prod.txt + testing/linting tools
  Dockerfile          Multi-stage: deps -> collectstatic -> non-root -> gunicorn
  .github/workflows/
    ci.yml            Lint + test on every PR
    deploy.yml        Test + deploy to Cloud Run on push to main
```

## Request Flow

```
Client Request
     │
     ├── /api/* ──→ DRF View ──→ Serializer (validate) ──→ Service Layer ──→ Model/DB
     │                                                          │
     └── /* ─────→ Web View ───────────────────────────────→ Service Layer ──→ Model/DB
                       │
                       └──→ Template (HTML response)
```

Both the API and web views call the **same service functions**. This is the DRY principle in action — booking logic exists in one place regardless of how users access it.

## The Services Layer

The `clinic/services/` package is the core of the application. It contains all business logic, free of HTTP concepts (no requests, responses, or status codes).

| Module              | Responsibility                                      |
| ------------------- | --------------------------------------------------- |
| `slots.py`        | Generate 30-min slot starts from times + timezone   |
| `availability.py` | Query booked slots + time-offs, return what's free  |
| `booking.py`      | Book, cancel, reschedule with full validation       |
| `appointments.py` | Read queries (upcoming for patient)                 |
| `exceptions.py`   | Domain errors carrying a message and an HTTP status |

**The services layer:**

To prevent duplicate validation logic in both `clinic/api/views.py` and `clinic/web/views.py`. The service layer has:

- One place to fix a bug in booking logic
- One place to add a new validation rule
- Views become thin adapters: parse input -> call service -> format output

## How Availability is Computed

```python
get_availability(doctor_id, date)
  1. Look up WorkingHours for that weekday
  2. Generate all 30-min slot starts (UTC) via slot_starts()
  3. Query booked appointments in that range
  4. Query time-offs overlapping that range
  5. Filter: not booked, not in time-off, not within 1hr of now
  6. Return free slots as UTC datetimes
```

This runs two DB queries (appointments + time-offs) then does set math in Python.

## How Booking Prevents Conflicts

```
Patient A books 09:00     Patient B books 09:00
      │                         │
      ▼                         ▼
  _validate_slot()          _validate_slot()
  (both pass)               (both pass)
      │                         │
      ▼                         ▼
  INSERT with               INSERT with
  transaction.atomic()      transaction.atomic()
      │                         │
      ▼                         ▼
  SUCCESS ✓                 IntegrityError!
  (row created)             (unique constraint violated)
                                │
                                ▼
                            SlotTaken -> 409
```

The database unique constraint is the authority which prevents double-booking under concurrency.

## Authentication Flow

```
Signup -> Create User (role=patient) + Create Patient -> Auto-login -> Redirect to appointments
Login -> Session auth (web) or JWT (API)
```

- **Web views**: Django session authentication. `@login_required` decorator.
- **API views**: JWT via `djangorestframework-simplejwt`. Token pair at `/api/token`.
- **Admin**: Django admin at `/admin/` for staff users.

## Timezone Handling

```
Storage:    UTC (all DateTimeFields)
Input:      Client sends local or UTC -> Django parses -> stores UTC
Display:    ClinicTimezoneMiddleware activates Africa/Nairobi -> templates render local time
API output: UTC
```

The `CLINIC_TIMEZONE` setting is a single constant.
