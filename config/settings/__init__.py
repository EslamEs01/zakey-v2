"""Environment dispatch for ZAKEY settings.

The historical entry point is ``DJANGO_SETTINGS_MODULE=config.settings`` (see
manage.py, wsgi.py, asgi.py and the Playwright webServer command). Keeping that
module importable means the split into base/development/production/test is
invisible to every existing run command, which is what preserves the storefront
tooling contract.

Select an environment with ``DJANGO_ENV=development|production|test``.
"""

from __future__ import annotations

import os

_ENV = os.environ.get("DJANGO_ENV", "development").strip().lower()

if _ENV == "production":
    from .production import *  # noqa: F401,F403
elif _ENV == "test":
    from .test import *  # noqa: F401,F403
elif _ENV == "development":
    from .development import *  # noqa: F401,F403
else:  # pragma: no cover - misconfiguration guard
    raise ValueError(
        f"Unknown DJANGO_ENV {_ENV!r}; expected 'development', 'production' or 'test'."
    )
