# Implementation Plan: ZAKEY Commerce Backend and Staff Administration

**Branch**: `004-zakey-commerce-backend-admin` | **Date**: 2026-08-04 | **Spec**: [spec.md](./spec.md)

## Summary

Add a modular Django commerce backend and a Jazzmin staff console beneath the approved ZAKEY storefront, without changing how that storefront looks or behaves. The work replaces a JSON fixture and browser `localStorage` with PostgreSQL-backed models, transaction-safe commerce services, and role-based administration — introduced in reversible batches, each gated on visual-regression and route-preservation evidence.

The two hard problems are (1) commerce integrity — no overselling, no duplicate orders, no lost money — solved with database constraints plus locked transactions rather than application checks alone; and (2) frontend preservation — solved by keeping template context keys stable so views change and templates barely do.

## Technical Context

**Language/Version**: Python 3.12 (pinned `>=3.12,<3.13`)
**Framework**: Django 5.2.16 (already pinned)
**Storage**: PostgreSQL 16+ (production and test). SQLite is not acceptable for concurrency evidence.
**Testing**: pytest + pytest-django + factory_boy; existing Playwright 1.62.1 suite retained unchanged
**Target Platform**: Linux server, server-rendered Django templates
**Project Type**: Server-rendered monolith with a modular app layout — no SPA, no public API
**Performance Goals**: catalogue p95 < 300 ms, product detail p95 < 400 ms, order creation p95 < 2 s at 20 concurrent
**Constraints**: zero visual drift at 1440/1024/768/390; all 13 routes preserved; Arabic-first RTL; no CDN; no SPA framework
**Scale/Scope**: ~9 seed products (built for thousands), 27 governorates, 12 apps, ~45 models, 9 staff roles

## Constitution Check

The 003 constitution governs the frontend. This feature is the separately-approved backend it anticipated.

| Principle | Status | How |
|---|---|---|
| I. Frontend approval gate and scope isolation | ✅ | 003 is complete and approved; this is the separate backend feature it explicitly deferred. `contracts/backend-handoff-boundary.md` listed exactly this scope as "deferred to a separately approved backend feature". |
| II. Reference fidelity and governed design system | ✅ | No design change. `contracts/frontend-preservation-boundary.md` defines the gate; every UI-touching task carries a 4-viewport visual check. |
| III. Arabic-first accessible responsive experience | ✅ | All new strings Arabic; server validation reuses the exact existing messages; axe gate retained. |
| IV. Replaceable prototype data and progressive enhancement | ✅ | This is the replacement the principle anticipated: `fixture_provider.py` and `storage-adapter.js` are the named seams. No-JS behaviour preserved (FR-136). |
| V. Evidence-based quality gates | ✅ | Every task states tests and required evidence; PostgreSQL concurrency evidence is mandatory. |

**Deviation**: adding shipping and installation rows to the order summary changes rendered numbers (FR-041, FR-062). Justified in `frontend-contract.md` §1.2 — the fixture contains no shipping price, so a real store cannot render a correct total without them. Bounded to adding rows inside the existing summary component using existing markup and label style. No restyle, no reorder.

## Project Structure

### Documentation

```text
specs/004-zakey-commerce-backend-admin/
├── spec.md                       # Requirements, stories, invariants
├── plan.md                       # This file
├── research.md                   # Architecture decisions
├── data-model.md                 # Models, constraints, indexes
├── tasks.md                      # 20 phases, granular tasks
├── quickstart.md                 # Developer setup
├── traceability.md               # FR → task → test
├── current-state-inventory.md    # What exists today
├── frontend-contract.md          # Protected contract
├── fixture-migration-map.md      # Fixture → model mapping
├── admin-model-matrix.md         # Per-model admin spec
├── permissions-matrix.md         # 9 roles × models
├── order-state-machine.md
├── payment-state-machine.md
├── inventory-integrity.md
├── security-threat-model.md
├── test-strategy.md
├── rollout-and-rollback.md
├── checklists/requirements.md
└── contracts/
    ├── storefront-data-contract.md
    ├── cart-checkout-contract.md
    ├── admin-operation-contract.md
    ├── payment-provider-boundary.md
    └── frontend-preservation-boundary.md
```

### Source code (repository root)

```text
config/
├── settings/
│   ├── __init__.py
│   ├── base.py            # replaces the current flat settings.py
│   ├── development.py
│   ├── production.py
│   └── test.py
├── urls.py                # unchanged route mounting
├── asgi.py
└── wsgi.py

apps/
├── core/          # SiteSetting, abstract bases, money utils, health, logging
├── accounts/      # User, CustomerProfile, Address, auth views
├── catalog/       # Category, Brand, Collection, Product, Variant, Image, …
├── inventory/     # StockItem, StockMovement, StockReservation, services
├── cart/          # Cart, CartLine, Wishlist, merge services
├── shipping/      # Governorate, ServiceArea, Zone, Method, Rate, Installation
├── promotions/    # Coupon, CouponRedemption, eligibility services
├── orders/        # Order, OrderLine, OrderAddress, Event, checkout services
├── payments/      # PaymentMethod, Payment, PaymentEvent, Refund, gateways
├── reviews/       # Review, moderation
├── content/       # HomeSection, Banner, FAQ, StaticPage, Navigation, …
└── audit/         # AuditLog, middleware, signals

storefront/        # EXISTING — views rewired to services, URLs unchanged
├── urls.py        # unchanged
├── views.py       # fixture calls → service calls, same context keys
└── fixture_provider.py   # retained until T-1608, then removed

templates/         # EXISTING — minimal, evidence-gated edits only
static/            # EXISTING — JS business rules removed, presentation kept
tests/
├── unit/          # models, constraints, money
├── integration/   # services, cart, checkout, orders
├── concurrency/   # PostgreSQL-only: locking, races, idempotency
├── admin/         # permissions, actions, query budgets
├── e2e/           # EXISTING Playwright — extended, not replaced
├── accessibility/ # EMPTY TODAY — populated in T-0102c
└── visual/        # EMPTY TODAY — framework built T-0102a, baselines T-0102b
```

**Structure Decision**: apps live under `apps/` to keep the repository root readable and to make the storefront's role obvious — `storefront/` is the presentation layer, `apps/` is the domain. `config/settings.py` becomes a `settings/` package (FR-001). `storefront/urls.py` is **not** touched, which is what guarantees route preservation (FR-131).

## Phasing

20 phases, detailed in [tasks.md](./tasks.md). Ordering is dependency-driven, and every phase is a checkpoint the user can inspect.

| # | Phase | Gate |
|---|---|---|
| 1 | Repository and frontend-contract freeze | Baseline screenshots captured at 4 viewports |
| 2 | Django foundation and configuration | PostgreSQL connects, `manage.py check --deploy` clean |
| 3 | Core shared models and utilities | Money and settings tests pass |
| 4 | Accounts and customer ownership | Auth, phone validation, IDOR tests pass |
| 5 | Catalogue | Models, constraints, admin CRUD |
| 6 | Inventory | Constraint + reservation tests pass |
| 7 | Cart and wishlist | Merge and recalculation tests pass |
| 8 | Shipping and installation | Zone, rate, eligibility tests pass |
| 9 | Promotions | Coupon eligibility + concurrency tests pass |
| 10 | Checkout and order integrity | **PostgreSQL concurrency suite green** |
| 11 | Payments and refunds | Refund limits + idempotency tests pass |
| 12 | Reviews and content | Moderation + content CRUD |
| 13 | Jazzmin configuration and administration | Dashboard bounded-query test passes |
| 14 | Permissions and auditing | 9-role matrix enforced server-side |
| 15 | Fixture migration and seed data | `seed_demo` idempotent, slugs preserved |
| 16 | Storefront integration | **Visual regression clean at 4 viewports** |
| 17 | Security hardening | Threat-model checklist closed |
| 18 | Tests and concurrency verification | Coverage ≥85%, 100% transitions |
| 19 | Visual-regression verification | Full 4-viewport, 13-route sweep |
| 20 | Production readiness and handoff | Runbook, rollback rehearsed |

Phases 1–3 are blocking. Phases 5–9 are largely parallelisable once 4 lands. Phase 10 depends on 5–9. Phase 16 is the highest-risk phase and is split into six independently revertible batches.

## Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **No visual-regression framework exists** | High | `tests/visual/` is empty and `site-integrity.spec.js` never diffs its screenshots (`current-state-inventory.md` §7). T-0102a **builds** the comparison framework before T-0102b captures baselines — the gate cannot be assumed to exist |
| **`FrontendBoundaryTests` blocks Phase 2** | High | `tests/test_fixture_provider.py:213-238` asserts the absence of the database, auth stack, sessions, admin and migrations — all inverted by this feature. T-0203a retires and replaces it in the same task that enables the auth stack |
| **CI does not run on this branch** | Medium | `pages.yml` triggers only on `main`/`003-*` with no `pull_request`. T-0207 adds the trigger before CI can gate anything |
| Visual drift during integration | High | 4-viewport baseline in Phase 1; per-batch gate; batches revert independently |
| Shipping/installation change the total | High | Explicitly scoped (FR-041/062), bounded to summary rows, business rates escalated (ASM-004/005) |
| Overselling under concurrency | High | DB constraint + `FOR UPDATE` + deterministic lock order + PostgreSQL tests |
| Duplicate orders | High | Unique idempotency key + insert-then-select |
| Route or slug drift | High | Route test asserts all 13 names/URLs; slug test asserts all 19 slugs |
| Kimi task overrun | Medium | Bounded ≤3 files/task, incremental output, verified by Claude (research.md §9) |
| Money precision errors | Medium | `Decimal` only; a lint/test forbids `float` in money paths |
| Admin N+1 at scale | Medium | Query-count assertions on every changelist |
| Scope creep from deferred list | Medium | `research.md` §10 is a parking lot, not a backlog |

## Complexity Tracking

| Deviation | Why needed | Simpler alternative rejected because |
|---|---|---|
| 12 apps instead of 1 | Distinct write patterns, locking and permission boundaries | One app makes permissions and audit scoping unmanageable and invites circular imports |
| 12 apps instead of the 15 proposed | Evidence-driven | `wishlist`, `checkout` and `notifications` had no models or no launch scope of their own (`research.md` §3) |
| Service layer for money/stock/state | These need transaction boundaries and locks | Model methods cannot express multi-model atomic operations cleanly |
| Snapshot fields on orders | History must survive catalogue change | FKs alone break historical accuracy (FR-067) |
| Separate `audit` app | Append-only with no dependencies | Per-app audit tables fragment the trail |
