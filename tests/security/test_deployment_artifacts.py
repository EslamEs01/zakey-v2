"""Deployment artifacts (T-2001–T-2004).

These files are only ever going to be read at the worst possible moment: during
a deploy, or during a restore after something has already gone wrong. So they
are tested like code.

Nothing here executes a privileged operation. Scripts are checked with `bash -n`
and exercised in `ZAKEY_DRY_RUN=1` mode inside temporary directories.

**No VPS was accessed and nothing was deployed.** These artifacts are reviewed
and locally validated; they are not evidence that any server exists.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from django.conf import settings

DEPLOY = Path(settings.BASE_DIR, "deploy")

SCRIPTS = ["zakey-deploy.sh", "zakey-backup.sh", "zakey-restore-drill.sh"]
CONFIGS = ["gunicorn.conf.py", "zakey-web.service", "zakey-nginx.conf"]

BASH = shutil.which("bash")


def read(name: str) -> str:
    return (DEPLOY / name).read_text(encoding="utf-8")


class TestArtifactsExist:
    @pytest.mark.parametrize("name", SCRIPTS + CONFIGS)
    def test_artifact_is_present(self, name):
        assert (DEPLOY / name).is_file(), f"deploy/{name} is missing"


@pytest.mark.skipif(BASH is None, reason="bash unavailable")
class TestScriptsAreValidAndFailFast:
    @pytest.mark.parametrize("name", SCRIPTS)
    def test_syntax_is_valid(self, name):
        result = subprocess.run(
            [BASH, "-n", str(DEPLOY / name)], capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr

    @pytest.mark.parametrize("name", SCRIPTS)
    def test_it_stops_on_failure(self, name):
        """`set -e` plus `-u` plus `-o pipefail`: no silent half-deploy."""
        head = read(name)
        assert re.search(r"^set -Eeuo pipefail$", head, re.M), (
            f"{name} does not fail fast"
        )

    @pytest.mark.parametrize("name", SCRIPTS)
    def test_it_contains_no_secret(self, name):
        text = read(name)
        pattern = re.compile(
            r"(?i)(secret_key|password|api[_-]?key|token)\s*=\s*[\"'][^\"'$\{]{8,}[\"']"
        )
        assert not pattern.search(text), f"{name} appears to embed a secret"

    @pytest.mark.parametrize("name", SCRIPTS)
    def test_it_names_zakey_explicitly(self, name):
        """A deploy script must not be able to act on another project."""
        assert "zakey" in read(name).lower()

    def test_the_deploy_script_never_seeds_demo_data(self):
        text = read("zakey-deploy.sh")
        invocations = re.findall(r"^\s*(?:run\s+)?.*manage\.py\s+seed_demo", text, re.M)
        assert invocations == [], f"deploy invokes seed_demo: {invocations}"

    def test_the_deploy_script_validates_every_required_variable(self):
        text = read("zakey-deploy.sh")
        for name in (
            "DJANGO_SECRET_KEY",
            "DJANGO_ALLOWED_HOSTS",
            "DATABASE_URL",
            "CSRF_TRUSTED_ORIGINS",
        ):
            assert f"require_env {name}" in text, f"{name} is not validated"

    def test_the_deploy_script_rejects_placeholder_values(self):
        text = read("zakey-deploy.sh")
        for marker in ("PLACEHOLDER", "changeme", "django-insecure-"):
            assert marker in text, f"placeholder guard for {marker!r} is missing"

    def test_the_deploy_script_refuses_sqlite(self):
        assert "SQLite is refused" in read("zakey-deploy.sh")


@pytest.mark.skipif(BASH is None, reason="bash unavailable")
class TestDryRunBehaviour:
    def _run(self, name, *args, env=None):
        environment = {**os.environ, "ZAKEY_DRY_RUN": "1"}
        environment.update(env or {})
        return subprocess.run(
            [BASH, str(DEPLOY / name), *args],
            capture_output=True, text=True, env=environment, timeout=60,
        )

    def test_validate_refuses_a_missing_secret(self):
        result = self._run(
            "zakey-deploy.sh", "validate",
            env={"DJANGO_SECRET_KEY": "", "DJANGO_ALLOWED_HOSTS": "zakey.test",
                 "DATABASE_URL": "postgres://u:p@h/zakey", "CSRF_TRUSTED_ORIGINS": "https://zakey.test"},
        )
        assert result.returncode != 0
        assert "DJANGO_SECRET_KEY" in result.stderr

    def test_validate_refuses_a_placeholder_secret(self):
        result = self._run(
            "zakey-deploy.sh", "validate",
            env={"DJANGO_SECRET_KEY": "django-insecure-" + "x" * 50,
                 "DJANGO_ALLOWED_HOSTS": "zakey.test",
                 "DATABASE_URL": "postgres://u:p@h/zakey",
                 "CSRF_TRUSTED_ORIGINS": "https://zakey.test"},
        )
        assert result.returncode != 0
        assert "placeholder" in result.stderr

    def test_validate_refuses_a_wildcard_host(self):
        result = self._run(
            "zakey-deploy.sh", "validate",
            env={"DJANGO_SECRET_KEY": "k" * 60, "DJANGO_ALLOWED_HOSTS": "*",
                 "DATABASE_URL": "postgres://u:p@h/zakey",
                 "CSRF_TRUSTED_ORIGINS": "https://zakey.test"},
        )
        assert result.returncode != 0

    def test_validate_refuses_a_non_postgres_database(self):
        result = self._run(
            "zakey-deploy.sh", "validate",
            env={"DJANGO_SECRET_KEY": "k" * 60, "DJANGO_ALLOWED_HOSTS": "zakey.test",
                 "DATABASE_URL": "sqlite:///zakey.db",
                 "CSRF_TRUSTED_ORIGINS": "https://zakey.test"},
        )
        assert result.returncode != 0
        assert "PostgreSQL" in result.stderr

    def test_validate_refuses_a_database_that_is_not_zakey(self):
        """It must not be possible to point the deploy at another project."""
        result = self._run(
            "zakey-deploy.sh", "validate",
            env={"DJANGO_SECRET_KEY": "k" * 60, "DJANGO_ALLOWED_HOSTS": "zakey.test",
                 "DATABASE_URL": "postgres://u:p@h/some_other_project",
                 "CSRF_TRUSTED_ORIGINS": "https://zakey.test"},
        )
        assert result.returncode != 0
        assert "zakey" in result.stderr

    def test_validate_accepts_a_well_formed_environment(self):
        result = self._run(
            "zakey-deploy.sh", "validate",
            env={"DJANGO_SECRET_KEY": "k" * 60, "DJANGO_ALLOWED_HOSTS": "zakey.example.eg",
                 "DATABASE_URL": "postgres://u:p@h/zakey",
                 "CSRF_TRUSTED_ORIGINS": "https://zakey.example.eg"},
        )
        assert result.returncode == 0, result.stderr

    def test_backup_refuses_a_foreign_database(self):
        result = self._run(
            "zakey-backup.sh",
            env={"DATABASE_URL": "postgres://u:p@h/another_project"},
        )
        assert result.returncode != 0
        assert "zakey" in result.stderr

    def test_backup_dry_run_writes_nothing(self, tmp_path):
        result = self._run(
            "zakey-backup.sh",
            env={"DATABASE_URL": "postgres://u:p@h/zakey",
                 "ZAKEY_BACKUP_DIR": str(tmp_path)},
        )
        assert result.returncode == 0, result.stderr
        assert list(tmp_path.iterdir()) == []

    def test_the_restore_drill_refuses_a_non_scratch_database(self):
        result = self._run(
            "zakey-restore-drill.sh", "/tmp/zakey.dump",
            env={"DATABASE_URL": "postgres://u:p@h/zakey",
                 "ZAKEY_SCRATCH_DB": "zakey"},
        )
        assert result.returncode != 0
        assert "scratch" in result.stderr

    def test_the_restore_drill_never_targets_the_live_database(self):
        text = read("zakey-restore-drill.sh")
        assert "refusing: DATABASE_URL points at the scratch database" in text
        assert "--dbname=\"$SCRATCH_DB\"" in text


class TestSystemdAndNginx:
    def test_the_unit_isolates_the_service(self):
        unit = read("zakey-web.service")
        for directive in (
            "NoNewPrivileges=true", "ProtectSystem=strict", "ProtectHome=true",
            "PrivateTmp=true",
        ):
            assert directive in unit, f"{directive} missing from the unit"

    def test_the_unit_writes_only_to_zakey_paths(self):
        unit = read("zakey-web.service")
        writable = re.search(r"^ReadWritePaths=(.*)$", unit, re.M)
        assert writable, "ReadWritePaths is not declared"
        for path in writable.group(1).split():
            assert path.startswith("/srv/zakey/"), f"{path} is outside the ZAKEY tree"

    def test_the_unit_takes_secrets_from_a_file_not_the_repository(self):
        unit = read("zakey-web.service")
        assert "EnvironmentFile=/etc/zakey/zakey.env" in unit
        assert "DJANGO_SECRET_KEY=" not in unit

    def test_nginx_denies_healthz_to_the_internet(self):
        conf = read("zakey-nginx.conf")
        block = conf[conf.index("location = /healthz/"):]
        assert "deny all;" in block[:400]

    def test_nginx_forces_https_and_sets_security_headers(self):
        conf = read("zakey-nginx.conf")
        assert "return 301 https://$host$request_uri;" in conf
        for header in ("Strict-Transport-Security", "X-Content-Type-Options",
                       "X-Frame-Options"):
            assert header in conf

    def test_nginx_refuses_to_execute_uploaded_media(self):
        conf = read("zakey-nginx.conf")
        assert re.search(r"location ~\* \\\.\(php\|py\|pl\|cgi\|sh\)\$", conf)

    def test_nginx_hostname_is_an_obvious_placeholder(self):
        """Nobody must be able to deploy this thinking the host is configured."""
        assert "ZAKEY_HOSTNAME_PLACEHOLDER" in read("zakey-nginx.conf")

    def test_gunicorn_binds_to_loopback_only(self):
        conf = read("gunicorn.conf.py")
        assert '"127.0.0.1:8001"' in conf

    def test_gunicorn_access_log_omits_query_strings_and_cookies(self):
        conf = read("gunicorn.conf.py")
        fmt = re.search(r"access_log_format = '(.*)'", conf).group(1)
        assert "%(q)s" not in fmt
        assert "Cookie" not in fmt


class TestEnvExample:
    def test_it_exists_and_names_every_required_variable(self):
        text = Path(settings.BASE_DIR, ".env.example").read_text(encoding="utf-8")
        for name in ("DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS", "DATABASE_URL"):
            assert name in text, f"{name} is not documented in .env.example"

    def test_the_example_secret_is_one_the_deploy_script_would_reject(self):
        """The property that matters, rather than a list of magic words.

        Any value in the example file must be refused by
        ``zakey-deploy.sh validate`` — otherwise someone could copy the example
        to production and the deploy would happily accept it.
        """
        text = Path(settings.BASE_DIR, ".env.example").read_text(encoding="utf-8")
        value = ""
        for line in text.splitlines():
            if line.startswith("DJANGO_SECRET_KEY="):
                value = line.split("=", 1)[1].strip().strip("\"'")

        rejected = (
            not value
            or len(value) < 50                       # deploy enforces >= 50
            or value.startswith("django-insecure-")
            or any(m in value.lower() for m in ("placeholder", "changeme", "insecure"))
        )
        assert rejected, (
            f"the example secret {value[:12]}... would pass deploy validation"
        )

    @pytest.mark.skipif(BASH is None, reason="bash unavailable")
    def test_the_example_env_is_rejected_end_to_end(self):
        """Proved by running the real validator against the real example file."""
        example = {}
        for line in Path(settings.BASE_DIR, ".env.example").read_text(
            encoding="utf-8"
        ).splitlines():
            if line.strip().startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            example[key.strip()] = val.strip().strip("\"'")

        result = subprocess.run(
            [BASH, str(DEPLOY / "zakey-deploy.sh"), "validate"],
            capture_output=True, text=True,
            env={**os.environ, "ZAKEY_DRY_RUN": "1", **example},
            timeout=60,
        )
        assert result.returncode != 0, (
            "the deploy validator accepted .env.example verbatim"
        )
