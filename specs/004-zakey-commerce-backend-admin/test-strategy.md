# Test Strategy

**Feature**: 004-zakey-commerce-backend-admin
Implements NFR-002 – NFR-013 and the SC-001 – SC-015 success criteria.

**Non-negotiable**: concurrency, locking, uniqueness-race and transaction behaviour are verified on **PostgreSQL only**. SQLite does not implement `SELECT … FOR UPDATE` and silently no-ops it — a green SQLite run is not evidence, it is a false negative (FR-002, NFR-005).

---

## 1. Layout

```
tests/
├── unit/           # models, constraints, money, validators
├── integration/    # services, cart, checkout, ownership
├── concurrency/    # PostgreSQL only — races, locks, idempotency
├── admin/          # registration, permissions, actions, query budgets
├── security/       # threat-model coverage
├── seed/           # fixture import, idempotency, slug preservation
├── e2e/            # EXISTING Playwright — extended
├── accessibility/  # EMPTY TODAY — populated in T-0102c
└── visual/         # EMPTY TODAY — framework built in T-0102a, baselines in T-0102b
```

Python: `pytest` + `pytest-django` + `factory_boy`. Existing suites in `tests/test_routes.py` and `tests/test_static_export.py` are kept and must keep passing throughout — they are the route-preservation tripwire.

> ⚠️ **Two corrections to the assumed baseline** (`current-state-inventory.md` §7):
>
> 1. **`tests/visual/`, `tests/accessibility/` and `tests/helpers/` are empty directories.** There is **no screenshot-diff framework** — `site-integrity.spec.js` captures screenshots as evidence but never compares them, and `npm run test:a11y` currently runs zero tests. The preservation gate below must be **built** in T-0102a/T-0102c before it can gate anything.
> 2. **`FrontendBoundaryTests` (`tests/test_fixture_provider.py:213-238`) must be retired, not preserved.** It asserts the absence of the database, auth stack, sessions, admin, `storefront.models` and migrations — the exact preconditions this feature removes. It is a phase guard, not a regression test. T-0203a retires it and replaces its intent with a rendering-contract test. The rest of `test_fixture_provider.py` (fixture contract and catalogue behaviour) stays until `fixture_provider.py` is removed in T-1608.

---

## 2. Unit

Model validation and every database constraint asserted by triggering `IntegrityError`, not by trusting `full_clean`:

- unique: product slug, variant SKU, order number, idempotency key, `provider_event_id`, `(cart, variant)`, `(coupon, order)`, `(product, customer)` review
- check: `reserved <= on_hand`, `on_hand >= 0`, quantity 1–9, rating 1–5, `amount > 0`, `compare_at_price > price`, one default address, one default variant
- money: `Decimal` throughout; VAT extraction `gross × 14 ÷ 114`; `ROUND_HALF_UP`; line totals quantized before summing; **a test asserts no `float` appears in any money path**
- validators: Egyptian mobile across `01012345678`, `+201012345678`, `0020…`, Arabic-Indic `٠١٠…`, and invalid prefixes (`013`, `014`) — must match `^01[0125]\d{8}$` after normalisation
- derived availability maps to `available` / `limited` / `unavailable` exactly as the storefront filter expects

## 3. Integration

- **Catalogue**: filter, sort, search, paginate — asserted **identical to `fixture_provider` output** for the canonical cases, including page size 6, `available` matching both `available` and `limited`, and AND-semantics feature facets (`catalogue.js:55`, `fixture_provider.py:167-172`)
- **Cart**: add, update, remove, quantity clamp, `(cart, variant)` identity, unavailable rejection, price recomputation, stale price surfaced
- **Cart merge**: anonymous + account carts, quantity summing, stock clamping, coupon retention
- **Coupon**: percentage, fixed, cap, window, usage limits, minimum basket, product/category restriction, case-insensitive input
- **Shipping**: zone rate resolution, free-shipping threshold on discounted subtotal, same-day area eligibility, installation governorate + per-line support
- **Checkout**: full server validation reproducing every Arabic message; each invalid field asserted individually
- **Orders**: creation, snapshots, event log, and **history correctness after the product is renamed, repriced and archived** (FR-067)
- **Ownership**: every customer-owned model asserts 404 on cross-user access (SC-007)

## 4. Concurrency — PostgreSQL, `TransactionTestCase` with real threads

| Test | Setup | Assertion |
|---|---|---|
| `test_no_overselling` | 1 unit, 20 concurrent checkouts | exactly 1 order, 19 clean failures, `available >= 0` always (SC-002) |
| `test_idempotent_checkout` | same key replayed 10× | exactly 1 order (SC-003) |
| `test_coupon_usage_limit_race` | limit 5, 20 concurrent | exactly 5 redemptions (SC-004) |
| `test_order_number_uniqueness_race` | 50 concurrent orders | 50 unique numbers, no collision |
| `test_multi_line_no_deadlock` | carts with variants {A,B} and {B,A} | both complete, no deadlock (lock ordering) |
| `test_refund_cannot_exceed_capture` | concurrent refunds | Σ refunds ≤ captured (SC-013) |
| `test_payment_callback_replay` | same `provider_event_id` twice | one `PaymentEvent` |
| `test_order_transition_concurrency` | two staff, two transitions | one winner, loser gets stale-state error |
| `test_stock_adjust_during_checkout` | admin adjust + checkout concurrently | no negative available |
| `test_reservation_expiry_idempotent` | sweeper run twice | second run releases nothing |

A CI job runs this directory against a real PostgreSQL service. **The suite fails loudly if the database backend is not PostgreSQL** rather than passing quietly.

## 5. Admin

Registration completeness; the full role × model × operation matrix from `permissions-matrix.md` §2 exercised by calling admin URLs as each user; read-only enforcement on order lines, order money, movements, payment events and audit log; every bulk action's validation and per-object reporting; **query-count budgets** on every changelist and on the dashboard (NFR-003); and a test proving that hiding a menu entry does not grant or deny access.

## 6. Security

One test per threat in `security-threat-model.md` §1: IDOR sweep, privilege escalation, price tampering, CSRF on every mutating endpoint, XSS payloads, upload rejection (magic bytes, oversize, SVG, decompression bomb), login rate limiting, open redirect, log redaction, and `check --deploy` returning zero issues.

## 7. Frontend preservation gate ★

Runs on every task that touches `templates/` or `static/`, and again in full at Phase 19.

| Check | Tool | Pass condition |
|---|---|---|
| Visual regression | Playwright screenshots | No unintended diff vs. Phase 1 baseline at **1440 / 1024 / 768 / 390** across all 13 routes (SC-008) |
| Route preservation | Django test | All 13 names and URLs resolve identically (SC-009) |
| Slug preservation | Django test | All 9 product + 6 collection + 4 category slugs resolve (SC-011) |
| Console errors | Playwright | Zero errors on every route × viewport (NFR-009) |
| Horizontal overflow | Playwright | `scrollWidth <= clientWidth` everywhere |
| RTL | Playwright | `dir="rtl"` intact; no LTR leakage |
| Accessibility | axe | No new critical or serious violation (NFR-007) |
| Asset loading | Playwright | No 404 on any asset |
| No-JS | Playwright | Existing `no-js` projects still pass (FR-136) |
| HTML validity | `html-validate` | `npm run check:html` clean |

The comparison framework is **built** in T-0102a (it does not exist today) and baselines are captured **before any backend work** in T-0102b. Any intended change — the shipping and installation rows of FR-041/FR-062 — is re-baselined deliberately, with the diff reviewed and approved by Claude and recorded in the task's evidence. Silent re-baselining is a review failure.

## 8. Seed

`seed_demo` twice → identical counts, zero duplicates (SC-010); every slug preserved (SC-011); every price exactly equal to the fixture; every image path resolving on disk; catalogue availability parity with `fixture_provider`; `--force` refusal when orders exist; and `Order.objects.count() == 0` after seeding (no fabricated orders, ASM-007).

## 9. Coverage and gates

- Services, models, permissions ≥ **85%** (NFR-013)
- **100%** of order and payment state transitions exercised (SC-005)
- Every FR traceable to ≥1 test (SC-014, `traceability.md`)
- CI: lint → unit → integration → admin → security → seed → **concurrency (PostgreSQL)** → `npm run qa`
- A task is complete only when its named tests pass **and** its evidence is attached. "Tests were not run" is a blocker, never a pass.

## 10. What is explicitly not weakened

Tests are never deleted, skipped or loosened to make a task pass. A failing test is either a real defect to fix or a specification error to escalate to Claude. Marking a test `xfail` requires Claude's written approval recorded in the task evidence.
