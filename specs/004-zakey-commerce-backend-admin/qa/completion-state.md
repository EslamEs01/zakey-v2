# Final-completion session state (compaction-durable)

Authoritative ledger: **143 total · 139 checked · 4 open** —
T-1806, T-1901, T-1906, T-2006. (**T-2003 closed this session.**)

## T-2003 — DONE

`tests/deployment/test_rollback_rehearsal.py` — 32 tests green. Record in
`qa/rollback-rehearsal.md`. Real scripts, real git releases A/B, real curl
against a real health endpoint, real PostgreSQL scratch restore; `systemctl`
and `uv` shimmed. **Found and fixed a real defect**: `rollback()` never entered
`ZAKEY_ROOT`, so `uv sync` and `collectstatic` ran in the operator's cwd.

Rebuild this picture at any time with:

```
grep -c '^- \[x\]' specs/004-zakey-commerce-backend-admin/tasks.md   # 139
grep -c '^- \[ \]' specs/004-zakey-commerce-backend-admin/tasks.md   #   4
uv run python scripts/traceability.py --check                        # T-1806 gate
```

## Blockers established this session (verified, not assumed)

| task | state | evidence |
|---|---|---|
| T-1901 | **BLOCKED — no image viewing** | the `Read` tool errors `No such tool available: Read. Read is disabled for this session, in subagents as well as here.` No other image-capable tool exists (ToolSearch returned only `ctx_overview`, `TaskList`, `WebFetch`). |

**T-1901 integrity check:** `git status --short tests/visual/` is **empty**. All
52 tracked snapshots still carry their pre-session timestamps (4–5 Aug). No
snapshot was updated, individually or in bulk; `--update-snapshots` was never
run. The comparison set was independently re-discovered this session and is
identical: `account` × 4 and `checkout` × 3, 89 passed / 7 failed. The 21 exact
PNG paths are tabulated in `qa/visual-approval-ledger.md` §0.
| T-1906 | **BLOCKED by T-1901 — proven, not assumed** | a full `npm run qa` was run this session: **505 passed, 7 failed, exit 1**, and the 7 failures are *exactly* the 7 visual comparisons (`account` ×4, `checkout` ×3). Every other stage — build, `check:js`, `check:matrix`, e2e, accessibility, no-JS, `check:html`, `check:evidence`, `test:pages` — passed. The gate goes green the moment T-1901 closes; nothing else stands in its way. |
| T-2006 | **BLOCKED — business input absent** | the session instruction carries the literal unfilled placeholder `[INSERT THE APPROVED SHIPPING AND INSTALLATION DECISION HERE]`, plus "Do not invent or infer any commercial value." No rate may be entered. |

### T-2006 — machinery verified ready, only the numbers are missing

Re-checked this session, so that entering the values is the *only* remaining step:

- `apps/shipping/services.py::has_unapproved_rates()` is the launch gate — true
  while any active `ShippingRate` or `InstallationService` is `is_placeholder`.
- `ZAKEY_ALLOW_PLACEHOLDER_RATES` defaults to **False** in
  `config/settings/production.py`, so production refuses to quote a placeholder.
- `tests/security/test_commercial_rate_gate.py` (26 tests) covers the gate,
  including FR-046/047/048 added this session — all using deliberately fake
  development values.

**Still required from the business** (verbatim from `handoff.md` §6):
1. **Shipping rates per zone**, for each active shipping method.
2. **The installation fee**, and the governorates where installation is offered.

## T-1806 — traceability

Mechanism (from `scripts/traceability.py`): evidence is attributed by an **AST
walk of test docstrings**. A requirement is proven when its ID appears in the
docstring of a test module, class or function. Closing a gap therefore means
naming the requirement in the docstring of a test that *actually asserts it*,
or writing that test where none exists.

Baseline at session start: 122 FRs · 122 claimed · **53 with evidence** ·
**68 problems** (all of form `FR-xxx: no test proves it`). The matrix header's
"76" was stale.

**Now: 122 claimed · 121 with evidence · 0 problems.** (122 − 121 = FR-135,
which is `📄` by design — a process artifact, not a gap.)

### T-1806 verification gates

| gate | result |
|---|---|
| `scripts/traceability.py --check` | **exit 0, 0 problems** |
| two consecutive runs from equivalent state | **byte-identical**, md5 `18f0c205be6937fbbe90f18b69247139`, both exit 0 |
| `scripts/verify_traceability_nodes.py` | **every mapped node collectible** (checked against `pytest --collect-only`) |
| orphans / false mappings | none — all 68 newly closed FRs reviewed personally; every one maps to a domain-correct file |
| full Python suite (1,902 tests) | 1,900 pass; 2 pre-existing **wall-clock** tests (`test_home_p95`, `test_login_form_failure_wall_time_is_equalised`) fail under machine load and pass in isolation — neither file was touched this session, neither is in `npm run qa` |

**T-1806 is closed.** Ledger now 140 checked / 3 open.

Narrative record: `qa/traceability-closure.md`. Divergences: `qa/spec-divergences.md`.

Closed by 8 parallel agents over disjoint FR ranges with exclusive file
ownership, then reviewed personally. New test files:
`test_catalogue_rules`, `test_seed_demo`, `test_movement_reasons`,
`test_returns_decision`, `test_addresses`, `test_provider_neutrality`,
`test_coupons`, `test_coupon_rules`, `test_order_creation`,
`test_order_snapshots`, `test_admin_readonly`, `test_cms_manageable`,
`test_context_keys`, `test_form_hardening`, `test_client_state_removal`.

### Two generator/precision fixes made this session

1. **`scripts/traceability.py` — narrowest claim wins.** A module docstring
   naming several requirements previously gave *every* test in the file to
   *each* of them: `test_admin_readonly.py` reported 26 tests for FR-105, FR-107,
   FR-108, FR-112 and FR-114 alike, and sampled evidence could cite a
   bulk-action test as proof of a read-only rule. A module-level claim now
   applies only to requirements no class or function in that file claims for
   itself. FR-105 → 7, FR-107 → 3, FR-114 → 8. **No requirement lost its
   mapping.**
2. **`scripts/verify_traceability_nodes.py` (new)** — asks pytest itself, via
   `--collect-only`, whether every mapped node ID is *collectible*, not merely
   AST-visible. Node IDs need exactly one `-q`: none prints a tree, two collapses
   to per-file counts, and `pyproject.toml`'s `addopts` already supplies one.
3. **`scripts/audit_module_level_claims.py` (new)** — reports module-level
   claims and whether narrower ones already cover them.

### Divergences found — see `qa/spec-divergences.md`

- **FR-086** resolved in code (expired/exhausted coupons now use the existing
  rejection message; nothing referenced the two removed strings).
- **FR-132** resolved by supersession (the adapter was removed in T-1608; no
  browser holds `zakey:prototype:v1` to migrate).
- **FR-025 is OPEN** — `mark_failed` never releases reservations, so the
  "payment failure" trigger is unimplemented. Deliberately not faked and not
  unilaterally "fixed": it is a product decision. Three of four triggers proven.

## T-2003 — rollback rehearsal

Isolated rehearsal only: temporary ZAKEY-only release directories, a scratch
PostgreSQL database, real `deploy/` rollback logic, mocked service-manager
boundary. No VPS, no real systemd, no production anything.
