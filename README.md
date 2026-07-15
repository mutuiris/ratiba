# Ratiba — Clinic Appointment Booking

[![Coverage Status](https://coveralls.io/repos/github/mutuiris/ratiba/badge.svg?branch=develop)](https://coveralls.io/github/mutuiris/ratiba?branch=develop)

Is an appointment system where patients browse doctors, view available 30-minute slots, and book/cancel/reschedule appointments. Built with Django, DRF, and PostgreSQL.

## Live Application

**https://ratiba-447993598243.africa-south1.run.app**

Demo credentials: `Addy` / `addy12345`

## Run Locally

Prerequisites: Python 3.13+, PostgreSQL

```bash
git clone https://github.com/mutuiris/ratiba.git
cd ratiba
python -m venv venv && source venv/bin/activate
pip install -r requirements/dev.txt

# Configure environment
cp .env.example .env  # then edit DATABASE_URL, SECRET_KEY

# Setup database
python manage.py migrate
python manage.py seed  # creates 5 doctors + demo patient + admin

# Run
python manage.py runserver
```

Visit http://localhost:8000 — login as `Addy`/`addy12345` (patient) or `admin`/`admin12345` (staff).

### Run Tests

```bash
pytest          # runs with coverage
ruff check .    # lint
ruff format .   # format
```

## Design Decisions

### Computed Slots (not stored rows)

Availability is computed on-the-fly from working hours rules — no `Slot` table that drifts out of sync when schedules change:

```
WorkingHours -> generate 30-min grid -> subtract booked -> subtract time-offs -> subtract too-soon
```

### Double-Booking Prevention

A partial unique index at the database level guarantees only one active booking per slot, even under concurrent requests:

```sql
UNIQUE(doctor, start_at) WHERE status='booked'
```

Two patients submitting the same slot simultaneously: the first `INSERT` wins, the second hits `IntegrityError` -> returns 409 Conflict.

### Atomic Reschedule

Rescheduling is a single `UPDATE` inside `transaction.atomic()` - the row never enters a "free" state. If the new slot is taken, `refresh_from_db()` restores the original. The patient always keeps an appointment.

### Compare-and-Set Cancel

```python
updated = Appointment.objects.filter(id=id, status="booked").update(status="cancelled", ...)
```

Check and write in one SQL statement. Two concurrent cancel requests: one gets `updated=1`, the other gets `updated=0` → raises `AlreadyCancelled`.

### UTC Storage, Local Display

All `DateTimeField` values store UTC. The `ClinicTimezoneMiddleware` activates `Africa/Nairobi` for template rendering. API always returns UTC - clients convert on their end.

### Services Layer

Both API views (DRF) and web views (server-rendered) call the same service functions in `clinic/services/`. Business logic exists in one place - views are thin adapters that parse input, call the service, and format output.

Full rationale: [docs/DESIGN.md](docs/DESIGN.md)

## CI/CD Pipeline

| Trigger                      | What happens                                                                          |
| ---------------------------- | ------------------------------------------------------------------------------------- |
| Pull request opened          | CI runs: ruff lint + format check + pytest against Postgres 17 service container      |
| Push to`develop`           | CI runs: same as above + coverage upload to Coveralls                                 |
| Merge`develop` → `prod` | Deploy runs: tests pass → Cloud Build builds image → Cloud Run deploys new revision |

- PRs are blocked on test failure
- `develop` is the integration branch; `prod` is the deployment branch
- Deployment uses **Workload Identity Federation** — no stored JSON keys; GitHub OIDC token exchanged for short-lived GCP credentials
- Runtime secrets fetched from **GCP Secret Manager** at container start (no env vars in Cloud Run config)
- Non-root container user (`app`) with bash entrypoint (`set -euo pipefail`)

## Documentation

| Document                            | Contents                                                 |
| ----------------------------------- | -------------------------------------------------------- |
| [System Design](docs/DESIGN.md)      | Models, slot strategy, trade-offs, concurrency decisions |
| [API Reference](docs/API.md)         | Endpoints with request/response examples                 |
| [Architecture](docs/ARCHITECTURE.md) | Request flow, services layer, folder structure           |
| [Deployment](docs/DEPLOYMENT.md)     | CI/CD pipeline, GCP setup, environment variables         |
| [AI Reflection](docs/REFLECTION.md)  | How AI was used, where it helped, where it was wrong     |

## Tech Stack

- **Backend**: Django 6.0, Django REST Framework 3.17, Python 3.13
- **Database**: PostgreSQL 17 (Cloud SQL)
- **Auth**: Session (web) + JWT (API) via SimpleJWT
- **Hosting**: Google Cloud Run (africa-south1)
- **CI/CD**: GitHub Actions + Workload Identity Federation
- **Static**: WhiteNoise
