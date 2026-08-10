"""Production settings (FR-004).

``python manage.py check --deploy`` must report zero issues under this module;
``tests/security/test_deploy_check.py`` asserts it rather than trusting review.
"""

from __future__ import annotations

from .base import *  # noqa: F401,F403
from .base import env, env_bool, env_list

DEBUG = False

SECRET_KEY = env("DJANGO_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY.startswith("insecure-"):
    raise ValueError(
        "DJANGO_SECRET_KEY must be set to a real secret in production (FR-001, threat T-11)."
    )

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if not ALLOWED_HOSTS:
    raise ValueError("DJANGO_ALLOWED_HOSTS must be set explicitly in production (FR-004).")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31_536_000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "config.storage.ZakeyManifestStaticFilesStorage"
    },
}

# Commercial shipping and installation rates are user-supplied business input
# (ASM-004, ASM-005). Production refuses to run on development placeholders so a
# placeholder can never be presented to a customer as a real price.
ZAKEY_ALLOW_PLACEHOLDER_RATES = env_bool("ZAKEY_ALLOW_PLACEHOLDER_RATES", False)
