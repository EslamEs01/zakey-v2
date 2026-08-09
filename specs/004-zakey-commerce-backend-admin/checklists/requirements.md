# Requirements Quality Checklist

**Purpose**: Verify the specification package is complete, unambiguous and implementation-ready before any code is written.
**Created**: 2026-08-04
**Feature**: [spec.md](../spec.md)
**Reviewer**: Claude

Every item was checked against repository evidence, not against intent. `[x]` means verified; a finding is recorded where one was found and corrected.

---

## Requirement completeness

- [x] CHK001 Every requirement is numbered and uniquely identified — 122 FR, 14 NFR
- [x] CHK002 Every requirement is testable and observable
- [x] CHK003 Requirements state MUST/MUST NOT, not aspiration
- [x] CHK004 No `[NEEDS CLARIFICATION]` marker remains
- [x] CHK005 Ambiguity resolved from evidence where possible — VAT inclusivity resolved from `cart.js:58` rather than assumed
- [x] CHK006 Unresolvable business values escalated, not invented — ASM-004/005 (shipping rates, installation fee)
- [x] CHK007 Every commerce domain from the brief is covered
- [x] CHK008 Exclusions are explicit
- [x] CHK009 Assumptions are explicit and evidence-linked
- [x] CHK010 Dependencies listed, with deliberate exclusions justified (`research.md` §6)

## Evidence grounding

- [x] CHK011 Current state documented before design — `current-state-inventory.md`
- [x] CHK012 Claims carry file and line citations
- [x] CHK013 Fixture contract extracted programmatically, not eyeballed
- [x] CHK014 Route inventory covers all 13 routes
- [x] CHK015 Form inventory covers all 18 templates
- [x] CHK016 JS business rules quoted with line numbers
- [x] CHK017 Absences stated explicitly (no CSRF, no `fetch`, no payment provider, no database)
- [x] CHK018 Delegated findings independently verified by Claude before acceptance — see `research.md` §9

## Domain coverage

- [x] CHK019 Catalogue: entities, states, slugs, ordering, variants, media
- [x] CHK020 Inventory: ledger, reservations, TTL, concurrency, audit
- [x] CHK021 Accounts: auth, phone validation, addresses, ownership
- [x] CHK022 Cart/wishlist: identity, merge, recalculation, expiry
- [x] CHK023 Pricing: VAT inclusive, Decimal, rounding, thresholds
- [x] CHK024 Shipping: 27 governorates, zones, rates, same-day, installation
- [x] CHK025 Checkout/orders: validation, atomicity, idempotency, snapshots, states
- [x] CHK026 Payments: provider-neutral, refund limits, idempotency, reconciliation
- [x] CHK027 Promotions: types, limits, restrictions, concurrency
- [x] CHK028 Reviews: rating, moderation, verified purchase, aggregates
- [x] CHK029 Content: settings, sections, FAQs, pages, navigation
- [x] CHK030 Administration: dashboard, menu, per-model matrix, actions
- [x] CHK031 Permissions: 9 roles × models × operations
- [x] CHK032 Security: 16 threats with controls and tests
- [x] CHK033 Migration: fixture mapping, idempotent seed, what is NOT seeded

## Integrity and correctness

- [x] CHK034 14 business invariants stated
- [x] CHK035 Each invariant enforced at the database, not only in application code
- [x] CHK036 Transaction boundaries specified per sensitive workflow
- [x] CHK037 Locked records named per workflow
- [x] CHK038 Deadlock avoidance specified (deterministic lock order by `variant_id`)
- [x] CHK039 Idempotency strategy per replayable operation
- [x] CHK040 Failure and retry behaviour specified
- [x] CHK041 Audit evidence specified per sensitive workflow
- [x] CHK042 Order state machine complete with an explicit rejection rule
- [x] CHK043 Payment state machine complete
- [x] CHK044 Money never uses binary floating point

## Frontend preservation

- [x] CHK045 Protected surface enumerated
- [x] CHK046 Permitted integration changes enumerated and closed-ended
- [x] CHK047 Forbidden changes enumerated
- [x] CHK048 Every visual delta identified, justified and bounded — exactly 2
- [x] CHK049 Preservation gate defined with pass conditions
- [x] CHK050 Gate applied to every UI-touching task
- [x] CHK051 4 viewports specified: 1440/1024/768/390
- [x] CHK052 Route and slug preservation is executable, not aspirational
- [x] CHK053 `data-*` hook surface baselined (139 attributes)
- [x] CHK054 Jazzmin confined to the admin, verified by a task

## Testing

- [x] CHK055 Test strategy covers every domain
- [x] CHK056 PostgreSQL mandated for concurrency evidence
- [x] CHK057 SQLite explicitly rejected as concurrency evidence
- [x] CHK058 10 named concurrency tests defined
- [x] CHK059 100% state-transition coverage required
- [x] CHK060 Permission matrix fully exercised
- [x] CHK061 Security tests map to threats
- [x] CHK062 Seed idempotency tested
- [x] CHK063 Coverage threshold set (85%)
- [x] CHK064 Test-weakening explicitly forbidden

## Task quality

- [x] CHK065 Tasks are atomic and dependency-ordered
- [x] CHK066 No oversized task ("implement all models") exists
- [x] CHK067 Each task names files that may and may not change
- [x] CHK068 Each task names tests and required evidence
- [x] CHK069 Each task has Kimi as executor and Claude as reviewer
- [x] CHK070 Visual-regression requirement present on every UI-touching task
- [x] CHK071 Rollback or recovery noted per risky task
- [x] CHK072 Migrations shipped with their model change
- [x] CHK073 No task is marked complete — all 143 unchecked
- [x] CHK074 Task sizing reflects the observed Kimi delegation limit (≤3 files)

## Traceability

- [x] CHK075 Every FR maps to ≥1 task
- [x] CHK076 Every FR maps to ≥1 test
- [x] CHK077 Every NFR maps to a task and verification
- [x] CHK078 Every invariant maps to an enforcement mechanism and a test
- [x] CHK079 Every success criterion maps to a verification
- [x] CHK080 Executor and reviewer recorded for every task

## Scope discipline

- [x] CHK081 Out-of-scope list explicit
- [x] CHK082 Deferred ideas parked separately (`research.md` §10)
- [x] CHK083 No unrequested infrastructure added
- [x] CHK084 Each excluded technology has a stated re-entry condition
- [x] CHK085 No payment-provider integration claimed
- [x] CHK086 No production deployment planned in this feature

---

## Findings raised and corrected during review

| # | Finding | Correction | Status |
|---|---|---|---|
| F-01 | Draft assumed prices were VAT-exclusive | Code proves extraction at `cart.js:58`; recorded as evidence-derived ASM-001 and FR-040 | ✅ Corrected |
| F-02 | Draft assumed shipping cost existed in the fixture | It does not — `shippingOptions` have no price. Raised as the contract gap in `frontend-contract.md` §1.2, scoped as FR-041/FR-062, escalated as ASM-004/005 | ✅ Corrected |
| F-03 | Draft carried the prototype's cart-line identity | `store.js:34,41` update/remove by `productId` only, breaking multi-finish carts. Corrected to `(cart, variant)` in FR-030 / T-0703 | ✅ Corrected |
| F-04 | Draft claimed a visual-regression baseline existed to extend | `tests/visual/` is **empty** and screenshots are never diffed. Split into T-0102a (build framework) + T-0102b (capture) | ✅ Corrected |
| F-05 | Draft claimed "existing tests pass unchanged" through Phase 2 | `FrontendBoundaryTests` asserts the absence of the database, auth stack and migrations — inverted by this feature. Added T-0203a to retire and replace it | ✅ Corrected |
| F-06 | Draft assumed CI would gate backend work | `pages.yml` triggers only on `main`/`003-*`. T-0207 rewritten to add the branch trigger first | ✅ Corrected |
| F-07 | Draft claimed 108 tasks | Actual count is **143**, verified by script | ✅ Corrected |
| F-10 | 5 FRs (029, 039, 040, 099, 135) were mapped in `traceability.md` but not annotated on any task line | Annotations added to T-0601, T-1701, T-0301, T-0704, T-1205 and the Phase-16 header | ✅ Corrected |
| F-11 | Security and handoff tasks appeared unmapped because `traceability.md` §1 indexes FRs only | Added §4b mapping every threat-based and process task explicitly | ✅ Corrected |
| F-08 | Draft proposed 15 apps from the brief | `wishlist`, `checkout` and `notifications` have no models or no launch scope; consolidated to 12 with reasons (`research.md` §3) | ✅ Corrected |
| F-09 | `npm run test:a11y` believed to provide a11y coverage | It targets an empty directory and runs zero tests; real axe coverage is inside `site-integrity.spec.js`. Added T-0102c | ✅ Corrected |

## Outcome

**86 checks passed. 11 findings raised, all corrected.** Two Spec Kit analysis passes were run; the second confirmed zero remaining coverage gaps (122/122 FRs annotated on tasks, 143/143 tasks traced). No unresolved material issue remains.

**The commercial input has since been decided (ASM-004/005, T-2006).** The approved launch is a **disabled-service** state, not a set of unfilled placeholders: free shipping for eligible orders at or above EGP 1,500, **no paid shipping** offered below it, and **installation switched off**, effective on the deployment date. `manage.py apply_launch_policy` applies it idempotently and audits the change; production refuses to start while any active rate is still a development placeholder. Paid shipping and installation are enabled later through the admin, with approved figures, as an explicit and audited act.
