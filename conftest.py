"""Session-wide pytest setup"""

from pathlib import Path

import pytest
from django.conf import settings


@pytest.fixture(autouse=True, scope="session")
def _ensure_static_root():
    Path(settings.STATIC_ROOT).mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def _disable_ssl_redirect(settings):
    """Prevent SECURE_SSL_REDIRECT from 301 all test requests in CI"""
    settings.SECURE_SSL_REDIRECT = False
