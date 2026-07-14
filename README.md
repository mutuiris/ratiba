# Ratiba — Clinic Appointment Booking

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
pytest          # runs with coverage (85% gate)
ruff check .    # lint
ruff format .   # format
```

## CI/CD Pipeline

| Trigger              | What happens                                                                          |
| -------------------- | ------------------------------------------------------------------------------------- |
| Pull request opened  | CI runs: lint + format check + tests against Postgres 17                              |
| PR merged to`main` | Deploy runs: tests pass → Cloud Build builds image → Cloud Run deploys new revision |

Pipeline blocks PRs on test failure. Deployment uses Workload Identity Federation (keyless auth from GitHub to GCP).

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
