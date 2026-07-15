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

## Branching Model

```
feature/* ──→ PR ──→ develop (CI runs) ──→ merge ──→ prod (Deploy runs)
```

- `develop` — integration branch, default. All PRs target here.
- `prod` — deployment branch. Only receives merges from `develop`, no direct commits.

## CI Pipeline (`.github/workflows/ci.yml`)

Triggers on **every pull request** and **push to `develop`**.

```
Checkout -> Setup Python 3.13 -> Install deps
  -> ruff check (lint)
  -> ruff format --check (formatting)
  -> migrate (against Postgres 17 service container)
  -> pytest with coverage (must pass 85% threshold)
  -> upload coverage to Coveralls
```

If any step fails, the PR is blocked from merging.

## Deploy Pipeline (`.github/workflows/deploy.yml`)

Triggers on **push to `prod`**.

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
- Workload Identity Federation — no stored JSON keys, GitHub OIDC token exchanged for short-lived GCP credentials

## How a Code Change Reaches Production

```
Feature branch → PR → CI runs (lint + test) → Review → Merge to develop
                                                              │
                                                     (when ready to deploy)
                                                              │
                                                              ▼
                                                   Merge develop → prod
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

The Dockerfile uses a multi-stage build:

1. **Builder stage**: pip wheel all dependencies from `requirements/prod.txt`
2. **Runtime stage**: install wheels (no compiler in image), copy source
3. Create `/app/staticfiles` with `app` ownership
4. Switch to non-root `app` user

**Entrypoint** (`entrypoint.sh` with `set -euo pipefail`):

```
collectstatic → migrate → seed → exec gunicorn (port 8080)
```

Cloud Run provides the `PORT=8080` environment variable and handles HTTPS termination.

## Runtime Secrets

Secrets are fetched from GCP Secret Manager at container start via `config/gcp_secrets.py`:

1. Checks for `K_SERVICE` env var
2. Uses `google.auth.default()` to resolve project ID
3. Fetches the `ratiba-env` secret (a single JSON blob)
4. Seeds `os.environ` with all key-value pairs

## Security

- HTTPS enforced via `SECURE_SSL_REDIRECT` (Cloud Run terminates TLS)
- HSTS enabled with 1-year max-age
- Secure session and CSRF cookies
- Non-root container user
- No stored service account keys (Workload Identity Federation)
- Secrets never in code or environment - injected from Secret Manager at runtime
