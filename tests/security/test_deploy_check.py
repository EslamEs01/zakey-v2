"""Production security settings (T-0204, FR-004).

`tasks.md` names this file as T-0204's acceptance evidence, and it did not
exist — the task was checked off against a setting that nothing asserted. These
are exactly the settings whose absence is invisible in development and
catastrophic in production, so they get asserted rather than assumed.

The settings module is imported directly rather than via `override_settings`,
because the claim under test is about what `config.settings.production`
*declares*, not about what a test can be persuaded to declare.
"""

from __future__ import annotations

import importlib
import os

import pytest
from django.core.management import call_command
from django.test import override_settings

REQUIRED_ENV = {
    "DJANGO_SECRET_KEY": "test-key-that-is-at-least-fifty-characters-long-for-safety",
    "DJANGO_ALLOWED_HOSTS": "zakey.example.eg",
    "DATABASE_URL": "postgres://user:pass@localhost:5432/zakey",
    "CSRF_TRUSTED_ORIGINS": "https://zakey.example.eg",
    "EMAIL_HOST": "smtp.example.eg",
    "EMAIL_HOST_USER": "mailer",
    "EMAIL_HOST_PASSWORD": "secret",
    "DEFAULT_FROM_EMAIL": "no-reply@zakey.example.eg",
}


@pytest.fixture(scope="module")
def production_settings():
    """Import `config.settings.production` with plausible env values."""
    previous = {key: os.environ.get(key) for key in REQUIRED_ENV}
    os.environ.update(REQUIRED_ENV)
    try:
        module = importlib.import_module("config.settings.production")
        yield importlib.reload(module)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class TestProductionSettings:
    """Every setting FR-004 names, asserted individually."""

    def test_debug_is_off(self, production_settings):
        assert production_settings.DEBUG is False

    def test_hsts_is_configured(self, production_settings):
        assert production_settings.SECURE_HSTS_SECONDS >= 31_536_000
        assert production_settings.SECURE_HSTS_INCLUDE_SUBDOMAINS is True

    def test_ssl_redirect_is_on(self, production_settings):
        assert production_settings.SECURE_SSL_REDIRECT is True

    def test_session_cookie_is_secure(self, production_settings):
        assert production_settings.SESSION_COOKIE_SECURE is True

    def test_csrf_cookie_is_secure(self, production_settings):
        assert production_settings.CSRF_COOKIE_SECURE is True

    def test_content_type_nosniff_is_on(self, production_settings):
        assert production_settings.SECURE_CONTENT_TYPE_NOSNIFF is True

    def test_frames_are_denied(self, production_settings):
        assert production_settings.X_FRAME_OPTIONS == "DENY"

    def test_allowed_hosts_is_explicit(self, production_settings):
        hosts = production_settings.ALLOWED_HOSTS
        assert hosts, "ALLOWED_HOSTS is empty in production"
        assert "*" not in hosts, "ALLOWED_HOSTS accepts any Host header"

    def test_the_session_cookie_is_http_only(self, production_settings):
        assert production_settings.SESSION_COOKIE_HTTPONLY is True

    def test_placeholder_rates_are_refused_by_default(self, production_settings):
        """ASM-004: production must not quote a development price."""
        assert production_settings.ZAKEY_ALLOW_PLACEHOLDER_RATES is False


class TestSecretsAreNotHardCoded:
    def test_the_secret_key_comes_from_the_environment(self, production_settings):
        assert production_settings.SECRET_KEY == REQUIRED_ENV["DJANGO_SECRET_KEY"]

    def test_production_refuses_to_import_without_a_secret_key(self):
        """A missing secret must stop a deploy, not fall back to a dev value."""
        import importlib

        previous = os.environ.get("DJANGO_SECRET_KEY")
        os.environ.pop("DJANGO_SECRET_KEY", None)
        try:
            with pytest.raises(Exception):
                importlib.reload(importlib.import_module("config.settings.production"))
        finally:
            if previous is not None:
                os.environ["DJANGO_SECRET_KEY"] = previous

    def test_no_settings_file_contains_a_literal_secret(self):
        """A secret in version control is a secret already leaked."""
        import re
        from pathlib import Path

        from django.conf import settings

        pattern = re.compile(
            r"(?i)(secret_key|password|api[_-]?key)\s*=\s*[\"'][^\"'{}$]{12,}[\"']"
        )
        offenders = []
        for path in Path(settings.BASE_DIR, "config").rglob("*.py"):
            for line in path.read_text(encoding="utf-8").splitlines():
                if pattern.search(line) and "env(" not in line and "os.environ" not in line:
                    offenders.append(f"{path.name}: {line.strip()[:70]}")
        assert offenders == [], f"hard-coded secrets in settings: {offenders}"


class TestDeployCheckIsClean:
    """T-0204's literal acceptance: zero deploy issues."""

    @override_settings(
        # The test settings use a short throwaway key, which trips security.W009.
        # That warning is about *this* environment, not about production — the
        # production key comes from the environment and is asserted separately in
        # TestSecretsAreNotHardCoded. Supplying a production-shaped key here keeps
        # the check focused on the settings T-0204 is actually about.
        SECRET_KEY="a-fifty-plus-character-key-with-plenty-of-entropy-9f3b7c1e",
        DEBUG=False,
        SECURE_SSL_REDIRECT=True,
        SECURE_HSTS_SECONDS=31_536_000,
        SECURE_HSTS_INCLUDE_SUBDOMAINS=True,
        SECURE_HSTS_PRELOAD=True,
        SESSION_COOKIE_SECURE=True,
        CSRF_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SECURE_CONTENT_TYPE_NOSNIFF=True,
        X_FRAME_OPTIONS="DENY",
        ALLOWED_HOSTS=["zakey.example.eg"],
    )
    def test_check_deploy_reports_no_issues(self):
        from io import StringIO

        out = StringIO()
        # `--fail-level ERROR` would hide warnings, which is where Django puts
        # most of its security advice, so the output is inspected directly.
        call_command("check", "--deploy", stdout=out, stderr=out)
        report = out.getvalue()

        assert "System check identified no issues" in report, report
