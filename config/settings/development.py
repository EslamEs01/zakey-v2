"""Local development settings."""

from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)

# Placeholder shipping/installation money is acceptable locally, and clearly
# labelled as such wherever it is displayed (ASM-004, ASM-005).
ZAKEY_ALLOW_PLACEHOLDER_RATES = True
