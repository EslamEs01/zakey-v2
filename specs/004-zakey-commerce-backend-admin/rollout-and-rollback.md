# Rollout and Rollback

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-135, NFR-011.

**No deployment occurs during this feature.** This document defines the procedure to be executed later, under separate approval.

---

## 1. Principles

1. **Reversible batches.** Every phase, and every Phase-16 batch, reverts on its own.
2. **Forward-only migrations**, additive first: add columns nullable, backfill, then constrain — never drop in the same release that stops writing.
3. **Gate before proceed.** A phase that fails its gate does not advance.
4. **The storefront must never be half-integrated in a customer-visible way** — each batch is a complete page group.
5. **Rehearse rollback before needing it.**

---

## 2. Sequence

| Stage | Content | Gate | Rollback |
|---|---|---|---|
| 0 | Baselines (Phase 1) | Screenshots + route contract captured | n/a |
| 1 | Foundation (Phases 2–3) | `check --deploy` clean; existing tests pass | Revert settings package |
| 2 | Domain models (Phases 4–12) | Unit + integration + **concurrency** green | Revert migrations (additive only, no data loss) |
| 3 | Administration (Phases 13–14) | Permission matrix + query budgets green | Revert admin modules; models untouched |
| 4 | Seed (Phase 15) | Idempotency + slug preservation proven | Truncate seeded tables; storefront still on fixtures |
| 5 | **Integration (Phase 16)** ★ | Per-batch visual + route + console gate | **Per-batch revert** |
| 6 | Hardening (Phases 17–18) | Security + coverage gates | Revert individual controls |
| 7 | Verification (Phase 19) | Full 4-viewport sweep | n/a |
| 8 | Handoff (Phase 20) | Runbook + rehearsed restore | n/a |

**Stages 1–4 are invisible to customers.** The storefront still renders from fixtures throughout, because `storefront/views.py` is not rewired until Stage 5. That is the point of the ordering: all the risk concentrates in one reversible stage.

---

## 3. Phase 16 batch strategy ★

| Batch | Pages | Revert blast radius |
|---|---|---|
| T-1601 | home, about, contact | 3 static-ish pages |
| T-1602 | shop, collection, search | catalogue only |
| T-1603 | product detail | one page |
| T-1604 | cart (+ shipping row) | cart only |
| T-1605 | checkout (+ installation row) | checkout only |
| T-1606 | account, wishlist | account only |

Each batch: implement → run the full preservation gate → Claude reviews the screenshot diff → accept or revert. A reverted batch leaves the others working, because each touches a disjoint set of view functions and templates.

**Feature flag**: `USE_DATABASE_STOREFRONT` (per batch) lets a batch be switched back to the fixture path without a code revert — the fastest possible rollback during Stage 5. The flag and `fixture_provider.py` are removed together in T-1608, only after all six batches are accepted.

---

## 4. Migration safety

- Additive first; nullable then backfilled then constrained.
- No `ALTER TABLE` that rewrites a large table during a release window.
- Indexes created `CONCURRENTLY` in production.
- Every migration reviewed for lock duration before it ships.
- Data migrations are idempotent and re-runnable.
- Reverse migrations provided wherever mechanically possible; where a reverse would lose data it is documented as forward-only and the rollback path is a restore.

---

## 5. Rollback playbook

| Failure | Action |
|---|---|
| Batch fails visual gate | Flip its feature flag / revert the batch commit |
| Migration fails mid-apply | Transactional DDL rolls back; fix and re-run |
| Data corruption suspected | Stop writes, restore from the nightly dump, replay from audit log |
| Overselling detected | Disable checkout, run `verify_stock_integrity`, reconcile, re-enable |
| Payment divergence | Run `reconcile_payments`, freeze refunds, resolve manually |
| Admin permission leak | Revert the group assignment, audit the exposure window via `AuditLog` |

**Backup**: nightly encrypted PostgreSQL dump, 30-day retention, plus media. **Restore must be rehearsed at least once before launch** (T-2002) — an unrehearsed backup is not a backup, it is a hope.

---

## 6. Post-launch monitoring

`/healthz`; error reporting; `reconcile_payments` and `verify_stock_integrity` on a schedule; alerts on failed payments, negative-stock attempts, permission denials and order-creation errors; a weekly report of orders, refunds and stock adjustments.

---

## 7. Go-live checklist

- [ ] All 20 phases complete and reviewed by Claude
- [ ] Full 4-viewport visual sweep passes with only the two approved deltas
- [ ] PostgreSQL concurrency suite green
- [ ] `check --deploy` reports zero issues
- [ ] Secrets in environment; none in the repository
- [ ] Backup taken **and restore rehearsed**
- [ ] Staff roles assigned and verified
- [ ] ⚠️ **Real shipping rates and installation fee entered** (T-2006, ASM-004/005) — placeholders must not reach customers
- [x] Rollback rehearsed — `qa/rollback-rehearsal.md` (T-2003)
- [ ] User has approved go-live
