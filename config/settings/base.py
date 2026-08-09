"""Shared settings for every environment.

Environment-specific modules import from here and override. Selection happens in
``config/settings/__init__.py`` via ``DJANGO_ENV`` so that the historical
``DJANGO_SETTINGS_MODULE=config.settings`` entry point keeps working.
"""

from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _load_dotenv(path: Path) -> None:
    """Populate os.environ from a .env file without adding a dependency.

    Existing environment variables always win, so a real environment cannot be
    silently overridden by a stray file.
    """
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_dotenv(BASE_DIR / ".env")


def env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


def env_bool(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_list(key: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(key, default).split(",") if item.strip()]


def database_from_url(url: str) -> dict[str, object]:
    """Parse a postgres:// URL into Django's DATABASES entry (FR-001, FR-002)."""
    parts = urlparse(url)
    if parts.scheme not in {"postgres", "postgresql"}:
        raise ValueError(
            f"Unsupported DATABASE_URL scheme {parts.scheme!r}; ZAKEY requires PostgreSQL (FR-002)."
        )
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(parts.path.lstrip("/")),
        "USER": unquote(parts.username or ""),
        "PASSWORD": unquote(parts.password or ""),
        "HOST": parts.hostname or "127.0.0.1",
        "PORT": str(parts.port or 5432),
        "CONN_MAX_AGE": 60,
        "ATOMIC_REQUESTS": False,
    }


# --- Core -------------------------------------------------------------------

SECRET_KEY = env("DJANGO_SECRET_KEY", "insecure-development-key-override-in-env")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost,testserver")

INSTALLED_APPS = [
    "jazzmin",  # must precede django.contrib.admin so it can theme it (FR-100)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Bulk catalogue maintenance in the admin (FR-104, T-1309).
    "import_export",
    # ZAKEY domain applications (the approved 12).
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.inventory",
    "apps.cart",
    "apps.shipping",
    "apps.promotions",
    "apps.orders",
    "apps.payments",
    "apps.reviews",
    "apps.content",
    "apps.audit",
    # Presentation layer.
    "storefront",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.audit.middleware.RequestIDMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": database_from_url(
        env("DATABASE_URL", "postgres://zakey@127.0.0.1:5433/zakey")
    )
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]

LOGIN_URL = "storefront:account"
LOGIN_REDIRECT_URL = "storefront:account"
LOGOUT_REDIRECT_URL = "storefront:home"

# --- Localisation (unchanged from the approved storefront) ------------------

LANGUAGE_CODE = "ar-eg"
TIME_ZONE = "Africa/Cairo"
USE_I18N = True
USE_TZ = True

# --- Static and media -------------------------------------------------------

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Upload hardening (threat T-08) -----------------------------------------

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000
ZAKEY_MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024
ZAKEY_MAX_DOCUMENT_UPLOAD_BYTES = 10 * 1024 * 1024
ZAKEY_ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
ZAKEY_ALLOWED_DOCUMENT_EXTENSIONS = [".pdf"]

# --- Commerce -----------------------------------------------------------------
# Runtime values live in core.SiteSetting (FR-005). These are only the bootstrap
# defaults used to seed that singleton, and the guard flags below.

ZAKEY_DEFAULT_VAT_RATE = "0.1400"
ZAKEY_DEFAULT_FREE_SHIPPING_THRESHOLD = "1500.00"
ZAKEY_DEFAULT_CURRENCY_CODE = "EGP"
ZAKEY_DEFAULT_CURRENCY_LABEL = "ج.م"
ZAKEY_MAX_LINE_QUANTITY = 9

# Shipping/installation money is NOT known commercially (ASM-004/ASM-005).
# Seeded values are development placeholders and must never reach production.
ZAKEY_ALLOW_PLACEHOLDER_RATES = True

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

EMAIL_BACKEND = env(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = env("DJANGO_DEFAULT_FROM_EMAIL", "no-reply@zakey.example")

# --- Jazzmin: STAFF ADMIN ONLY (FR-100) -------------------------------------
# Jazzmin themes django.contrib.admin. It is never loaded by, linked from, or
# allowed to influence the public storefront, which keeps its own approved
# Tailwind design system untouched.

# django-import-export is default-insecure: with no permission code set, ANY
# staff member who can open the admin can import or export ANY registered model,
# straight past the role matrix (FR-111). Binding the two actions to real model
# permissions is what closes that: exporting is a bulk read, importing is a bulk
# write, so they require `view` and `change` respectively.
IMPORT_EXPORT_IMPORT_PERMISSION_CODE = "change"
IMPORT_EXPORT_EXPORT_PERMISSION_CODE = "view"

JAZZMIN_SETTINGS = {
    "site_title": "إدارة زاكي",
    "site_header": "زاكي",
    "site_brand": "ZAKEY",
    "welcome_sign": "لوحة إدارة متجر زاكي",
    "copyright": "ZAKEY",
    "search_model": ["catalog.Product", "orders.Order", "accounts.CustomerProfile"],
    "show_ui_builder": False,
    "changeform_format": "horizontal_tabs",
    # Menu grouping per admin-model-matrix.md §1.
    "order_with_respect_to": [
        "core",
        "catalog",
        "inventory",
        "orders",
        "payments",
        "accounts",
        "shipping",
        "promotions",
        "reviews",
        "content",
        "audit",
    ],
    "icons": {
        "core.SiteSetting": "fas fa-cog",
        "catalog.Product": "fas fa-box",
        "catalog.ProductVariant": "fas fa-palette",
        "catalog.Category": "fas fa-sitemap",
        "catalog.Collection": "fas fa-layer-group",
        "catalog.Brand": "fas fa-tag",
        "inventory.StockItem": "fas fa-warehouse",
        "inventory.StockMovement": "fas fa-exchange-alt",
        "inventory.StockReservation": "fas fa-hourglass-half",
        "orders.Order": "fas fa-receipt",
        "orders.OrderEvent": "fas fa-history",
        "payments.Payment": "fas fa-credit-card",
        "payments.Refund": "fas fa-undo",
        "payments.PaymentMethod": "fas fa-wallet",
        "accounts.User": "fas fa-user",
        "accounts.CustomerProfile": "fas fa-id-card",
        "accounts.Address": "fas fa-map-marker-alt",
        "shipping.Governorate": "fas fa-map",
        "shipping.ShippingRate": "fas fa-truck",
        "shipping.InstallationService": "fas fa-tools",
        "promotions.Coupon": "fas fa-percent",
        "reviews.Review": "fas fa-star",
        "content.FAQ": "fas fa-question-circle",
        "audit.AuditLog": "fas fa-shield-alt",
    },
    "hide_models": [],
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "dark_mode_theme": None,
    "navbar_small_text": False,
    "body_small_text": False,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"redact": {"()": "apps.core.logging.RedactingFilter"}},
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s %(name)s %(request_id)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["redact"],
            "formatter": "structured",
        }
    },
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", "INFO")},
}
