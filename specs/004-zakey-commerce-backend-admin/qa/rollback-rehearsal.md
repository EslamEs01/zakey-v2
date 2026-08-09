# Rollback rehearsal record — T-2003

`rollout-and-rollback.md` §1.5 says *"rehearse rollback before needing it"* and
§7 gates go-live on it. This is the record of that rehearsal actually being
executed, not a description of how it would go.

Harness: `tests/deployment/test_rollback_rehearsal.py` — **32 tests, all green**.
It is a test module rather than a one-off script so the rehearsal is repeatable
and re-runs on every suite.

```
uv run pytest tests/deployment/test_rollback_rehearsal.py -q
................................                                         [100%]
```

## 1. What was real and what was mocked

| element | real / mocked | why |
|---|---|---|
| `deploy/zakey-deploy.sh` | **real**, unmodified, `ZAKEY_DRY_RUN=0` | dry-run only echoes; it cannot fail the way a rollback fails |
| `deploy/zakey-restore-drill.sh` | **real**, `ZAKEY_DRY_RUN=0` | same |
| Release A → release B | **real git repository** in a temp release root | the rollback mechanism *is* `git checkout --detach` |
| Health endpoint | **real HTTP server** on 127.0.0.1:8001, polled by **real `curl`** | the health gate is the only thing standing between a broken rollback and a silent success |
| PostgreSQL | **real** — `createdb`, `pg_dump`, `pg_restore`, `psql` on scratch databases | a restore that has never run is a hypothesis |
| `systemctl` | **mocked** (recording shim, failure-injectable) | needs an init system and root; the rehearsal asserts the right unit at the right point |
| `uv` | **mocked** (recording shim, records its cwd) | rebuilding a virtualenv proves nothing about rollback — but *where* it runs does |

**No VPS, no real systemd, no production database, no remote host.** Every
artefact lives under `tmp_path`; every database name is scratch-prefixed and
dropped on teardown.

## 2. Defect found by the rehearsal — and fixed

`rollback()` never entered `ZAKEY_ROOT`.

`deploy()` has always had `[ "$DRY_RUN" = "1" ] || cd "$ZAKEY_ROOT"`. `rollback()`
did not. It checked out the old revision with `git -C "$ZAKEY_ROOT"` — correctly
targeted — and then ran

```
uv sync --frozen --no-dev
uv run python manage.py collectstatic --noinput
```

in **whatever directory the operator happened to be standing in**. On the VPS,
step 4 of the handoff runbook is `deploy/zakey-deploy.sh deploy`, so an operator
rolling back is most likely sitting in `/srv/zakey` and would never notice. From
anywhere else — `/root`, `/home/…`, a second checkout — the rollback would
restart the service against **unsynced dependencies and stale static files**, and
report success, because the health check only proves the process answers.

Dry-run mode could not have caught this: `run()` echoes without executing, so the
working directory never mattered.

Fixed in `deploy/zakey-deploy.sh` using `deploy()`'s own idiom, and locked by
`TestReleaseRollback::test_dependency_and_static_steps_run_inside_the_release_root`,
which asserts the shim's recorded cwd is the release root.

## 3. What the rehearsal proves

### Release B → release A

| assertion | test |
|---|---|
| a live release B returns to release A on disk and at HEAD | `test_release_b_rolls_back_to_release_a` |
| the named unit is restarted | `test_the_service_is_restarted_by_name` |
| health is polled against a real endpoint | `test_health_is_verified_against_a_real_endpoint` |
| dependency + static steps run in the release root | `test_dependency_and_static_steps_run_inside_the_release_root` |
| order is code → service → health | `test_the_recorded_order_is_code_then_service_then_health` |

### Failure paths

| failure | required behaviour | test |
|---|---|---|
| no revision given | refuse, code unmoved | `test_a_missing_revision_is_refused` |
| unknown revision | abort **before** restarting | `test_an_unknown_revision_aborts_before_restarting` |
| health check returns 503 | non-zero exit, no success line | `test_a_failed_health_check_fails_the_rollback` |
| service manager refuses | non-zero exit, health never polled | `test_a_refused_service_restart_fails_the_rollback` |
| dependency sync fails | stop before the restart | `test_a_failed_dependency_sync_stops_before_the_restart` |
| unknown action | refuse | `test_an_unknown_action_is_refused` |

### Environment gate — 12 parametrised cases

Missing `DJANGO_SECRET_KEY` / `DJANGO_ALLOWED_HOSTS` / `DATABASE_URL` /
`CSRF_TRUSTED_ORIGINS`; placeholder secret; `django-insecure-` secret; secret
under 50 characters; wildcard hosts; `example.com` hosts; SQLite URL; a
PostgreSQL URL that does not name a zakey database; `DEBUG=1`.

Each asserts **both halves**: the script refuses, *and* release B is still
checked out with zero external commands executed. Validation happens before any
code moves — a rollback that half-runs on a bad environment is worse than one
that never started.

### Database restore

| assertion | test |
|---|---|
| a faithful dump restores and verifies on all 6 tables | `test_a_faithful_dump_restores_and_verifies` |
| the scratch database is dropped afterwards | `test_the_scratch_database_is_dropped_afterwards` |
| a dump that lost rows is reported as **not proven** | `test_a_dump_that_lost_rows_is_reported_as_unproven` |
| a non-scratch database name is refused | `test_a_database_not_named_as_scratch_is_refused` |
| `DATABASE_URL` pointing at the scratch DB is refused | `test_a_database_url_pointing_at_the_scratch_database_is_refused` |
| a missing dump is refused | `test_a_missing_dump_is_refused` |
| an unset `DATABASE_URL` is refused | `test_an_unset_database_url_is_refused` |
| no dump argument is refused | `test_no_dump_argument_is_refused` |

## 4. Limits of this rehearsal — stated, not hidden

- The service-manager boundary is mocked. The rehearsal proves the script asks
  for the right restart at the right moment and handles a refusal; it does not
  prove the unit file starts gunicorn on a real host. `zakey-web.service` is
  covered separately by `tests/security/test_deployment_artifacts.py`.
- `uv sync` is mocked, so the rehearsal proves *where* and *when* dependencies
  are synced, not that the lockfile resolves on the target platform.
- The restore drill ran against synthetic tables carrying the drill's six
  names, not a production-shaped dump. It proves the drill's comparison and all
  of its refusals; a production dump's schema is exercised by T-2002.
- `rollback` still deliberately does not revert the database. That is the
  documented design (additive migrations; an older revision runs against a newer
  schema), and the script prints the caveat. The restore path above is the
  answer when the schema must also go back.
