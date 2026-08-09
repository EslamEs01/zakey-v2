"""Production-like rollback rehearsal (T-2003).

`rollout-and-rollback.md` §5 promises a rollback playbook and §7 requires it to
be *rehearsed* before go-live. A playbook nobody has executed is a paragraph,
not a procedure — the same argument `zakey-restore-drill.sh` makes about
backups. This module executes it.

What is **real** here:

* `deploy/zakey-deploy.sh` and `deploy/zakey-restore-drill.sh` — the shipping
  scripts, run unmodified, with `ZAKEY_DRY_RUN=0`. Dry-run mode only echoes;
  it cannot fail the way a real rollback fails, so it proves nothing.
* **Two real releases in a real git repository.** Release B is checked out;
  the rollback must land the working tree back on release A.
* **A real HTTP health endpoint** on 127.0.0.1:8001, polled by a real `curl`.
  The script's health gate is verified by serving 200 and then 503.
* **Real PostgreSQL**: `createdb`, `pg_dump`, `pg_restore`, `psql` against a
  scratch database, for the restore half of the playbook.

What is **mocked**, and why:

* `systemctl` — the service-manager boundary. Restarting a unit needs an init
  system and root; the rehearsal asserts the *right* unit is restarted at the
  *right* point, and injects a restart failure.
* `uv` — the dependency-sync and `collectstatic` boundary. Rebuilding a
  virtualenv proves nothing about rollback, but *where* it runs does, so the
  shim records its working directory.

Nothing here touches a VPS, real systemd, the production database, or the
repository's own working tree. Every artefact lives in a temporary directory
and every database name is scratch-prefixed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from django.conf import settings

DEPLOY = Path(settings.BASE_DIR, "deploy")
DEPLOY_SH = DEPLOY / "zakey-deploy.sh"
RESTORE_DRILL = DEPLOY / "zakey-restore-drill.sh"

BASH = shutil.which("bash")
GIT = shutil.which("git")
CURL = shutil.which("curl")

HEALTH_PORT = 8001
HEALTH_PATH = "/healthz/"

#: An environment that `validate_environment` must accept. Deliberately
#: synthetic: the host is `.test`, and the secret is neither the example value
#: nor a placeholder pattern.
GOOD_ENV = {
    "DJANGO_SECRET_KEY": "z" * 64,
    "DJANGO_ALLOWED_HOSTS": "shop.zakey.test",
    "DATABASE_URL": "postgres://zakey@127.0.0.1:5433/zakey",
    "CSRF_TRUSTED_ORIGINS": "https://shop.zakey.test",
    "DEBUG": "0",
}

#: The tables `zakey-restore-drill.sh` compares. Losing any of them is the
#: unrecoverable case the drill exists to catch.
DRILL_TABLES = [
    "orders_order",
    "orders_orderline",
    "payments_payment",
    "payments_refund",
    "audit_auditlog",
    "catalog_product",
]

pytestmark = [
    pytest.mark.skipif(not BASH, reason="bash is required to run the deploy scripts"),
    pytest.mark.skipif(not GIT, reason="git is required to build the release repository"),
]


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------


class _HealthHandler(BaseHTTPRequestHandler):
    """Serves the health endpoint the rollback script actually polls."""

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's interface
        self.server.requests.append(self.path)
        status = self.server.status
        body = b"ok" if status == 200 else b"unhealthy"
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep pytest output readable
        return


@pytest.fixture
def health():
    """A real HTTP server on the port the script hard-codes."""
    server = ThreadingHTTPServer(("127.0.0.1", HEALTH_PORT), _HealthHandler)
    server.status = 200
    server.requests = []
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


class _Shims:
    def __init__(self, bin_dir: Path, journal: Path):
        self.bin = bin_dir
        self.journal = journal

    def calls(self) -> list[str]:
        if not self.journal.exists():
            return []
        return [ln for ln in self.journal.read_text().splitlines() if ln.strip()]

    def call_with(self, needle: str) -> str | None:
        return next((c for c in self.calls() if needle in c), None)


@pytest.fixture
def shims(tmp_path: Path) -> _Shims:
    """`systemctl` and `uv` stand-ins that record how they were invoked."""
    bin_dir = tmp_path / "shim-bin"
    bin_dir.mkdir()
    journal = tmp_path / "shim-journal.log"

    template = (
        "#!/usr/bin/env bash\n"
        'printf "%s %s :: cwd=%s\\n" "{name}" "$*" "$PWD" >> "$ZAKEY_REHEARSAL_JOURNAL"\n'
        'if [ "${{{fail_var}:-0}}" = "1" ]; then\n'
        '  echo "{name}: simulated failure" >&2\n'
        "  exit 1\n"
        "fi\n"
        "exit 0\n"
    )
    for name, fail_var in (("systemctl", "ZAKEY_FAIL_SYSTEMCTL"), ("uv", "ZAKEY_FAIL_UV")):
        path = bin_dir / name
        path.write_text(template.format(name=name, fail_var=fail_var))
        path.chmod(0o755)

    return _Shims(bin_dir, journal)


def _git(repo: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "rehearsal",
        "GIT_AUTHOR_EMAIL": "rehearsal@zakey.test",
        "GIT_COMMITTER_NAME": "rehearsal",
        "GIT_COMMITTER_EMAIL": "rehearsal@zakey.test",
    }
    done = subprocess.run(
        [GIT, "-C", str(repo), *args], env=env, capture_output=True, text=True, check=True
    )
    return done.stdout.strip()


class _Releases:
    def __init__(self, root: Path, rev_a: str, rev_b: str):
        self.root = root
        self.rev_a = rev_a
        self.rev_b = rev_b

    @property
    def marker(self) -> str:
        return (self.root / "RELEASE").read_text().strip()

    def head(self) -> str:
        return _git(self.root, "rev-parse", "HEAD")


@pytest.fixture
def releases(tmp_path: Path) -> _Releases:
    """A ZAKEY-only release root holding two real releases, checked out at B."""
    root = tmp_path / "srv-zakey"
    root.mkdir()
    _git(root, "init", "--quiet", "--initial-branch=main")
    _git(root, "config", "user.email", "rehearsal@zakey.test")
    _git(root, "config", "user.name", "rehearsal")

    (root / "RELEASE").write_text("A\n")
    (root / "manage.py").write_text("# release A\n")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "release A")
    rev_a = _git(root, "rev-parse", "HEAD")

    (root / "RELEASE").write_text("B\n")
    (root / "manage.py").write_text("# release B\n")
    _git(root, "add", ".")
    _git(root, "commit", "--quiet", "-m", "release B")
    rev_b = _git(root, "rev-parse", "HEAD")

    assert (root / "RELEASE").read_text().strip() == "B"
    return _Releases(root, rev_a, rev_b)


def run_deploy_script(
    action: str,
    *args: str,
    releases: _Releases,
    shims: _Shims,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run the real script with mocked service-manager and dependency tooling."""
    full_env = {
        **os.environ,
        **GOOD_ENV,
        "ZAKEY_ROOT": str(releases.root),
        "ZAKEY_SERVICE": "zakey-web",
        "ZAKEY_DRY_RUN": "0",
        "ZAKEY_REHEARSAL_JOURNAL": str(shims.journal),
        "PATH": f"{shims.bin}{os.pathsep}{os.environ['PATH']}",
    }
    for key, value in (env or {}).items():
        if value is None:
            full_env.pop(key, None)
        else:
            full_env[key] = value

    return subprocess.run(
        [BASH, str(DEPLOY_SH), action, *args],
        env=full_env,
        capture_output=True,
        text=True,
        cwd=str(Path(settings.BASE_DIR)),
    )


# ---------------------------------------------------------------------------
# 1. The rehearsal proper — release B rolls back to release A
# ---------------------------------------------------------------------------


class TestReleaseRollback:
    def test_release_b_rolls_back_to_release_a(self, releases, shims, health):
        """The whole point: a live release B is returned to release A."""
        assert releases.marker == "B"

        done = run_deploy_script(
            "rollback", releases.rev_a, releases=releases, shims=shims
        )

        assert done.returncode == 0, done.stderr
        assert releases.marker == "A"
        assert releases.head() == releases.rev_a
        assert "rolled back to" in done.stdout

    def test_the_service_is_restarted_by_name(self, releases, shims, health):
        run_deploy_script("rollback", releases.rev_a, releases=releases, shims=shims)

        restart = shims.call_with("systemctl restart zakey-web")
        assert restart is not None, f"service was never restarted: {shims.calls()}"

    def test_health_is_verified_against_a_real_endpoint(self, releases, shims, health):
        """The health gate must actually poll; a rollback that skips it is blind."""
        done = run_deploy_script(
            "rollback", releases.rev_a, releases=releases, shims=shims
        )

        assert done.returncode == 0, done.stderr
        assert health.requests == [HEALTH_PATH], health.requests

    def test_dependency_and_static_steps_run_inside_the_release_root(
        self, releases, shims, health
    ):
        """`uv` must run in the release root, not in the operator's shell cwd.

        The script is invoked from wherever the operator happens to stand. If
        the dependency sync and `collectstatic` do not enter ``ZAKEY_ROOT``
        first, they operate on the wrong project — silently, because `uv` is
        perfectly happy to sync whatever it finds.
        """
        run_deploy_script("rollback", releases.rev_a, releases=releases, shims=shims)

        uv_calls = [c for c in shims.calls() if c.startswith("uv ")]
        assert uv_calls, "dependency sync and collectstatic never ran"
        for call in uv_calls:
            assert f"cwd={releases.root}" in call, call

    def test_the_recorded_order_is_code_then_service_then_health(
        self, releases, shims, health
    ):
        """Restarting before the code moves would serve the old release."""
        done = run_deploy_script(
            "rollback", releases.rev_a, releases=releases, shims=shims
        )
        assert done.returncode == 0, done.stderr

        calls = shims.calls()
        sync = next(i for i, c in enumerate(calls) if c.startswith("uv sync"))
        static = next(i for i, c in enumerate(calls) if "collectstatic" in c)
        restart = next(i for i, c in enumerate(calls) if c.startswith("systemctl restart"))
        assert sync < static < restart
        # curl is real, so the health poll is ordered by the server's own record.
        assert health.requests == [HEALTH_PATH]


# ---------------------------------------------------------------------------
# 2. Failure paths — every branch that must refuse
# ---------------------------------------------------------------------------


class TestRollbackFailurePaths:
    def test_a_missing_revision_is_refused(self, releases, shims, health):
        done = run_deploy_script("rollback", releases=releases, shims=shims)

        assert done.returncode != 0
        assert "usage" in done.stderr.lower()
        assert releases.marker == "B", "a refused rollback must not move the code"

    def test_an_unknown_revision_aborts_before_restarting(self, releases, shims, health):
        done = run_deploy_script(
            "rollback", "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
            releases=releases, shims=shims,
        )

        assert done.returncode != 0
        assert releases.marker == "B"
        assert shims.call_with("systemctl restart") is None, "restarted despite a failed checkout"

    def test_a_failed_health_check_fails_the_rollback(self, releases, shims, health):
        """A rollback that cannot prove the service is up must not report success."""
        health.status = 503

        done = run_deploy_script(
            "rollback", releases.rev_a, releases=releases, shims=shims
        )

        assert done.returncode != 0
        assert "rolled back to" not in done.stdout
        assert health.requests == [HEALTH_PATH]
        # The code did move; that is why the operator needs the non-zero exit.
        assert releases.marker == "A"

    def test_a_refused_service_restart_fails_the_rollback(self, releases, shims, health):
        done = run_deploy_script(
            "rollback", releases.rev_a,
            releases=releases, shims=shims,
            env={"ZAKEY_FAIL_SYSTEMCTL": "1"},
        )

        assert done.returncode != 0
        assert "rolled back to" not in done.stdout
        assert health.requests == [], "health was polled after a failed restart"

    def test_a_failed_dependency_sync_stops_before_the_restart(
        self, releases, shims, health
    ):
        done = run_deploy_script(
            "rollback", releases.rev_a,
            releases=releases, shims=shims,
            env={"ZAKEY_FAIL_UV": "1"},
        )

        assert done.returncode != 0
        assert shims.call_with("systemctl restart") is None

    def test_an_unknown_action_is_refused(self, releases, shims, health):
        done = run_deploy_script("frobnicate", releases=releases, shims=shims)

        assert done.returncode != 0
        assert "unknown action" in done.stderr


class TestEnvironmentGate:
    """Validation must happen *before* any code moves.

    Each case asserts both halves: the script refuses, and release B is still
    checked out. A rollback that half-runs on a bad environment is worse than
    one that never started.
    """

    @pytest.mark.parametrize(
        ("override", "expected"),
        [
            pytest.param({"DJANGO_SECRET_KEY": None}, "DJANGO_SECRET_KEY", id="secret-missing"),
            pytest.param({"DJANGO_ALLOWED_HOSTS": None}, "DJANGO_ALLOWED_HOSTS", id="hosts-missing"),
            pytest.param({"DATABASE_URL": None}, "DATABASE_URL", id="database-missing"),
            pytest.param({"CSRF_TRUSTED_ORIGINS": None}, "CSRF_TRUSTED_ORIGINS", id="csrf-missing"),
            pytest.param(
                {"DJANGO_SECRET_KEY": "PLACEHOLDER" + "x" * 60}, "placeholder", id="secret-placeholder"
            ),
            pytest.param(
                {"DJANGO_SECRET_KEY": "django-insecure-" + "x" * 60},
                "placeholder",
                id="secret-django-insecure",
            ),
            pytest.param({"DJANGO_SECRET_KEY": "z" * 49}, "shorter than 50", id="secret-too-short"),
            pytest.param({"DJANGO_ALLOWED_HOSTS": "*"}, "wildcard", id="hosts-wildcard"),
            pytest.param(
                {"DJANGO_ALLOWED_HOSTS": "shop.example.com"}, "placeholder", id="hosts-example-com"
            ),
            pytest.param(
                {"DATABASE_URL": "sqlite:///zakey.db"}, "PostgreSQL", id="database-sqlite"
            ),
            pytest.param(
                {"DATABASE_URL": "postgres://u@127.0.0.1:5433/someotherdb"},
                "does not name a zakey database",
                id="database-not-zakey",
            ),
            pytest.param({"DEBUG": "1"}, "DEBUG=1", id="debug-enabled"),
        ],
    )
    def test_a_bad_environment_refuses_before_the_code_moves(
        self, releases, shims, health, override, expected
    ):
        done = run_deploy_script(
            "rollback", releases.rev_a, releases=releases, shims=shims, env=override
        )

        assert done.returncode != 0
        assert expected in done.stderr, done.stderr
        assert releases.marker == "B", "the release moved despite a rejected environment"
        assert shims.calls() == [], "external commands ran despite a rejected environment"

    def test_the_good_environment_is_accepted(self, releases, shims, health):
        """Guards the negatives above: they must fail for their stated reason."""
        done = run_deploy_script("validate", releases=releases, shims=shims)

        assert done.returncode == 0, done.stderr
        assert "environment OK" in done.stdout


# ---------------------------------------------------------------------------
# 3. The database half — restore into a scratch PostgreSQL database
# ---------------------------------------------------------------------------
#
# `zakey-deploy.sh rollback` deliberately does *not* touch the database: an
# older revision runs against a newer additive schema. The playbook's answer to
# "the schema must go back too" is a restore, so the rehearsal is incomplete
# until a restore has actually been performed and verified.

PG_TOOLS = ["psql", "pg_dump", "pg_restore", "createdb", "dropdb"]
MISSING_PG = [t for t in PG_TOOLS if not shutil.which(t)]

pg_required = pytest.mark.skipif(
    bool(MISSING_PG), reason=f"PostgreSQL client tools missing: {MISSING_PG}"
)


def _pg_env() -> dict[str, str]:
    """Point libpq at the local disposable cluster (`scripts/dev-db.sh`)."""
    env = {**os.environ}
    env.pop("PGDATABASE", None)
    env.setdefault("PGHOST", "127.0.0.1")
    env.setdefault("PGPORT", "5433")
    env.setdefault("PGUSER", "zakey")
    return env


def _psql(dbname: str, sql: str) -> str:
    done = subprocess.run(
        ["psql", "-d", dbname, "-tAc", sql],
        env=_pg_env(), capture_output=True, text=True, check=True,
    )
    return done.stdout.strip()


def _database_exists(dbname: str) -> bool:
    out = subprocess.run(
        ["psql", "-d", "postgres", "-tAc",
         f"SELECT 1 FROM pg_database WHERE datname = '{dbname}'"],
        env=_pg_env(), capture_output=True, text=True,
    )
    return out.stdout.strip() == "1"


def _drop(dbname: str) -> None:
    subprocess.run(["dropdb", "--if-exists", dbname], env=_pg_env(), capture_output=True)


@pytest.fixture
def source_db():
    """A throwaway source database carrying the tables the drill compares."""
    name = f"zakey_rehearsal_src_{uuid.uuid4().hex[:10]}"
    subprocess.run(["createdb", name], env=_pg_env(), capture_output=True, check=True)
    try:
        for table in DRILL_TABLES:
            _psql(name, f"CREATE TABLE {table} (id serial PRIMARY KEY, note text)")
        # Distinct row counts, so a mismatch names the table it happened in.
        for offset, table in enumerate(DRILL_TABLES, start=1):
            values = ",".join(f"('{table}-{i}')" for i in range(offset))
            _psql(name, f"INSERT INTO {table} (note) VALUES {values}")
        yield name
    finally:
        _drop(name)


@pytest.fixture
def scratch_db_name():
    name = f"zakey_scratch_{uuid.uuid4().hex[:10]}"
    yield name
    _drop(name)


@pytest.fixture
def dump_file(tmp_path, source_db):
    path = tmp_path / "zakey.dump"
    subprocess.run(
        ["pg_dump", "--format=custom", "--file", str(path), source_db],
        env=_pg_env(), capture_output=True, text=True, check=True,
    )
    assert path.exists() and path.stat().st_size > 0
    return path


def run_restore_drill(dump, scratch, database_url, extra_env=None):
    env = {
        **_pg_env(),
        "ZAKEY_SCRATCH_DB": scratch,
        "DATABASE_URL": database_url,
        "ZAKEY_DRY_RUN": "0",
        **(extra_env or {}),
    }
    return subprocess.run(
        [BASH, str(RESTORE_DRILL), str(dump)],
        env=env, capture_output=True, text=True,
    )


def _url_for(dbname: str) -> str:
    return f"postgres://zakey@127.0.0.1:5433/{dbname}"


@pg_required
class TestDatabaseRestore:
    def test_a_faithful_dump_restores_and_verifies(
        self, dump_file, scratch_db_name, source_db
    ):
        """The restore half of the playbook, actually executed."""
        done = run_restore_drill(dump_file, scratch_db_name, _url_for(source_db))

        assert done.returncode == 0, done.stderr
        assert "restore verified" in done.stdout
        for table in DRILL_TABLES:
            assert f"OK   {table}" in done.stdout, done.stdout

    def test_the_scratch_database_is_dropped_afterwards(
        self, dump_file, scratch_db_name, source_db
    ):
        """A drill that leaves databases behind becomes a drill nobody runs."""
        run_restore_drill(dump_file, scratch_db_name, _url_for(source_db))

        assert not _database_exists(scratch_db_name)

    def test_a_dump_that_lost_rows_is_reported_as_unproven(
        self, dump_file, scratch_db_name, source_db
    ):
        """The case the drill exists for: a restore that 'works' but loses orders."""
        _psql(source_db, "INSERT INTO orders_order (note) VALUES ('written after the dump')")

        done = run_restore_drill(dump_file, scratch_db_name, _url_for(source_db))

        assert done.returncode != 0
        assert "FAIL orders_order" in done.stderr
        assert "is NOT proven" in done.stderr
        assert "restore verified" not in done.stdout

    def test_a_database_not_named_as_scratch_is_refused(
        self, dump_file, source_db
    ):
        """The worst thing this script could do is restore over a live database."""
        done = run_restore_drill(dump_file, "zakey", _url_for(source_db))

        assert done.returncode != 0
        assert "not named as a scratch database" in done.stderr
        assert _database_exists(source_db), "the source database was touched"

    def test_a_database_url_pointing_at_the_scratch_database_is_refused(
        self, dump_file, scratch_db_name
    ):
        done = run_restore_drill(dump_file, scratch_db_name, _url_for(scratch_db_name))

        assert done.returncode != 0
        assert "DATABASE_URL points at the scratch database" in done.stderr

    def test_a_missing_dump_is_refused(self, tmp_path, scratch_db_name, source_db):
        done = run_restore_drill(
            tmp_path / "no-such.dump", scratch_db_name, _url_for(source_db)
        )

        assert done.returncode != 0
        assert "dump not found" in done.stderr
        assert not _database_exists(scratch_db_name)

    def test_an_unset_database_url_is_refused(self, dump_file, scratch_db_name):
        env = {**_pg_env(), "ZAKEY_SCRATCH_DB": scratch_db_name, "ZAKEY_DRY_RUN": "0"}
        env.pop("DATABASE_URL", None)
        done = subprocess.run(
            [BASH, str(RESTORE_DRILL), str(dump_file)],
            env=env, capture_output=True, text=True,
        )

        assert done.returncode != 0
        assert "DATABASE_URL is required" in done.stderr

    def test_no_dump_argument_is_refused(self, scratch_db_name, source_db):
        done = subprocess.run(
            [BASH, str(RESTORE_DRILL)],
            env={**_pg_env(), "ZAKEY_SCRATCH_DB": scratch_db_name,
                 "DATABASE_URL": _url_for(source_db)},
            capture_output=True, text=True,
        )

        assert done.returncode != 0
        assert "usage" in done.stderr.lower()
