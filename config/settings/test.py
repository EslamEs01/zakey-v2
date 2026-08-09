"""Test settings.

PostgreSQL is mandatory: SQLite silently ignores ``SELECT ... FOR UPDATE`` so a
green SQLite run would be a false negative for every concurrency guarantee
(FR-002, NFR-005). ``apps/core/tests/test_settings_split.py`` asserts this.
"""

from __future__ import annotations

from .base import *  # noqa: F401,F403

DEBUG = False

# Fast, deterministic hashing for tests only.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

ZAKEY_ALLOW_PLACEHOLDER_RATES = True
