# Final-completion session state (compaction-durable)

Ledger: **143 total · 142 checked · 1 open** — only **T-1906**, the two
consecutive green QA runs.

Rebuild this picture at any time:

```
grep -c '^- \[x\]' specs/004-zakey-commerce-backend-admin/tasks.md   # 142
grep -c '^- \[ \]' specs/004-zakey-commerce-backend-admin/tasks.md   #   1
uv run python scripts/traceability.py --check                        # exit 0
npx playwright test ./tests/visual                                   # 96 passed
```

## Closed in earlier passes of this session

* **T-2003** — rollback rehearsal, 32 tests. Real scripts, real git releases
  A/B, real `curl` against a real health endpoint, real PostgreSQL scratch
  restore; `systemctl` and `uv` shimmed. Found and fixed a real defect:
  `rollback()` never entered `ZAKEY_ROOT`. Record: `qa/rollback-rehearsal.md`.
* **T-1806** — traceability. 122 FRs · 122 claimed · 121 with evidence ·
  **0 problems**; two byte-identical `--check` runs, exit 0 both; every mapped
  node collectible. Records: `qa/traceability-closure.md`,
  `qa/spec-divergences.md` (all five divergences resolved).

## T-1901 — closed: visual inspection, 96 passed / 0 failed

All 21 images opened and inspected through the Codex CLI's image input (Claude's
own `Read` is disabled here). Record: `qa/visual-approval-record.md`.

* **checkout ×3 — genuine product regression, fixed, baselines untouched.**
  `.checkout-stepper-wrap` carries `padding-block: 42px 34px` = **exactly 76px**.
  The stepper is correctly suppressed on an empty basket (its `aria-controls`
  would dangle), but the padded wrapper still rendered, pushing the empty-state
  card down by precisely 76px. The class is now applied only when there is a
  stepper. All three pass against their **original** baselines.
* **account ×4 — correct intentional production change, approved individually.**
  The prototype's demo-only email card (`نسخة العرض`, `name@example.com`, "no
  real authentication exists") replaced by real sign-in, registration and
  password reset (FR-050/053/054).
  * Found on the way: `.account-auth`, `.account-auth-grid`, `.account-auth-card`
    had **no CSS at all** — source or build. Fixed by adopting `surface-card`
    (the canonical card) plus layout-only rules.
  * Also found: the approved **benefits card had been deleted**. Restored
    verbatim from the approved storefront.
  * Baselines replaced **one file at a time** with the exact reviewed bytes. No
    blanket `--update-snapshots` was ever run.
* Third defect, caught by `material-states`: Django `{# … #}` is **single-line
  only**; multi-line comments rendered as visible text on two pages. Now
  `{% comment %}`.

## T-2006 — closed: approved commercial launch policy applied

A **disabled-service launch**, not unfilled placeholders: EGP · VAT 14% · free
shipping at or above **EGP 1,500** · **no paid shipping** below it · installation
**disabled** · effective on the deployment date.

* `manage.py apply_launch_policy` — idempotent, `--dry-run`, writes an `AuditLog`
  naming every change and the accountable staff member. **Deliberately not in
  `zakey-deploy.sh`**: re-running a deploy must not silently withdraw paid
  shipping once the business approves it.
* `ShippingRate.free_threshold_only` + a `CheckConstraint` pinning such a rate to
  price 0, so paid shipping cannot reappear below the threshold via one edit.
* Below the threshold the customer is **refused, not invented for** —
  `FulfillmentUnavailable` naming the qualifying amount; the method is not even
  listed.
* Installation does not render on checkout while off; a forced POST is refused.
* `apps/shipping/checks.py` — `zakey.shipping.E001` fails production startup
  while any *active* rate is a placeholder; `W001` warns when paid shipping goes
  live. Tolerant of an unmigrated database.
* `ZAKEY_ALLOW_PLACEHOLDER_RATES` still defaults **False** in production.
* Tests: `tests/security/test_launch_policy.py`.

## Open

**T-1906** — two consecutive complete `npm run qa` runs, both exit 0:

```
ZAKEY_E2E_BASE_URL=http://127.0.0.1:8012 \
ZAKEY_E2E_SERVER_COMMAND='uv run python manage.py runserver 127.0.0.1:8012 --noreload' \
npm run qa
```

Port 8000 is held by an unrelated project on this machine; the private port is
the only reason those variables are set.
