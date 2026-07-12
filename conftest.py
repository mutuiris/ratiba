"""Session-wide pytest setup"""

from pathlib import Path

import pytest
from django.conf import settings


@pytest.fixture(autouse=True, scope="session")
def _ensure_static_root():
    # WhiteNoise warns if STATIC_ROOT is missing, so create it for the test run
    Path(settings.STATIC_ROOT).mkdir(parents=True, exist_ok=True)
