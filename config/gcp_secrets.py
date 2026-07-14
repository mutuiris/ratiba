"""Seed os.environ from a Secret Manager JSON blob when running on Cloud Run"""

import json
import os

SECRET_NAME = "ratiba-env"


def load_secrets() -> None:
    """Populate os.environ from Secret Manager when running on Cloud Run"""
    if not os.environ.get("K_SERVICE"):
        return

    import google.auth
    from google.cloud import secretmanager

    _, project_id = google.auth.default()
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    payload = json.loads(response.payload.data.decode("UTF-8"))

    for key, value in payload.items():
        os.environ.setdefault(key, str(value))
