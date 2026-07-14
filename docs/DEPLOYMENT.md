# Deployment & CI/CD

## Live URL

**https://ratiba-447993598243.africa-south1.run.app**

## Infrastructure

| Component            | Service                                |
| -------------------- | -------------------------------------- |
| Application          | Google Cloud Run (africa-south1)       |
| Database             | Cloud SQL for PostgreSQL 17            |
| Container Registry   | Artifact Registry                      |
| CI/CD                | GitHub Actions                         |
| Secrets              | GCP Secret Manager                     |
| Auth (GitHub → GCP) | Workload Identity Federation (keyless) |

## CI Pipeline (`.github/workflows/ci.yml`)

Triggers on **every pull request** and **push to main**.

```
Checkout -> Setup Python 3.13 -> Install deps
  -> ruff check (lint)
  -> ruff format --check (formatting)
  -> migrate (against Postgres 17 service container)
  -> pytest with coverage (must pass 85% threshold)
```

If any step fails, the PR is blocked from merging.

## Deploy Pipeline (`.github/workflows/deploy.yml`)

Triggers on **push to main**.

```
Job 1: test (same as CI — lint + format + test)
    ↓ (must pass)
Job 2: deploy
  → Authenticate via Workload Identity Federation
  → gcloud run deploy --source=. (Cloud Build builds image, deploys to Cloud Run)
```

**Key design choices:**

- Deploy only runs after tests pass (`needs: test`)
- `concurrency: cancel-in-progress` ensures only one deploy runs at a time
- Workload Identity Federation - no stored JSON keys, GitHub OIDC token exchanged for short-lived GCP credentials

## How a Code Change Reaches Production

```
Feature branch → PR → CI runs (lint + test) → Review → Merge to main
                                                              │
                                                              ▼
                                                   Deploy workflow triggers
                                                              │
                                                              ▼
                                                   Tests run again (gate)
                                                              │
                                                              ▼
                                                   Cloud Build: Docker build
                                                              │
                                                              ▼
                                                   Cloud Run: new revision live
```

## Environment Variables

| Variable                 | Where Set      | Purpose                                  |
| ------------------------ | -------------- | ---------------------------------------- |
| `SECRET_KEY`           | Secret Manager | Django secret key                        |
| `DATABASE_URL`         | Secret Manager | PostgreSQL connection (Cloud SQL socket) |
| `DEBUG`                | Cloud Run env  | Always`False` in production            |
| `ALLOWED_HOSTS`        | Cloud Run env  | Accepted hostnames                       |
| `CSRF_TRUSTED_ORIGINS` | Cloud Run env  | Trusted origins for CSRF                 |

## Container

The Dockerfile uses a multi stage approach:

1. Install Python dependencies from `requirements/prod.txt`
2. Copy source and run `collectstatic` (with dummy SECRET_KEY)
3. Switch to non-root `app` user
4. CMD: `migrate -> seed -> gunicorn` on port 8080

Cloud Run provides the `PORT=8080` environment variable and handles HTTPS termination.

## Security

- HTTPS enforced via `SECURE_SSL_REDIRECT` (Cloud Run terminates TLS)
- HSTS enabled with 1-year max-age
- Secure session and CSRF cookies
- Non-root container user
- No stored service account keys (Workload Identity Federation)
- Secrets never in code or environment - injected from Secret Manager at runtime
