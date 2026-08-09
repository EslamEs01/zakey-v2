# Contract: Admin Operations

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-100 – FR-115.

What staff may do, what the system guarantees while they do it, and what nobody may do.

---

## 1. Operating principles

1. **Server-side enforcement.** Every permission is checked in querysets, `has_*_permission` and action handlers. A hidden menu link is presentation, never protection (FR-111).
2. **Calculated values are read-only.** Totals, VAT, stock levels, aggregates and snapshots change only through validated services (FR-105).
3. **Financial and historical records are append-only.** Order lines, order money, payment events, stock movements and audit records have no edit path.
4. **Every mutation is audited** with actor, before, after, timestamp and request id (FR-113).
5. **Bounded queries.** No admin screen may scan an unbounded table (FR-102, FR-106).
6. **Bulk actions report per object** — never silent partial success (FR-107).

---

## 2. Core workflows

### Create a product
One screen: Product form + 6 inlines (variants, images, features, spec groups, documents, relations). Saves as `draft`. Publishing requires ≥1 variant and ≥1 image (FR-015). Slug validated unique; SKU validated globally unique. Audited.
*Roles*: Super, Store Manager, Catalogue Manager.

### Adjust stock
Never by typing a new level. The `adjust_stock` action opens an intermediate page requiring **delta + reason** (9 enumerated reasons). Executes under `select_for_update()`, rejects results where `on_hand < reserved` (naming how many are reserved), and writes a `StockMovement` plus an `AuditLog`.
*Roles*: Super, Store Manager, Inventory Manager.

### Process an order
Open → review read-only snapshots → apply a transition action. Every action validates against `order-state-machine.md`; invalid transitions are refused with the allowed set shown. Each writes an `OrderEvent`. Fulfilment converts reservations to deductions.
*Roles*: Super, Store Manager, Order Fulfilment.

### Record a payment
`record_payment` action: amount, method, reference. Validates the order is not cancelled and the amount does not exceed the outstanding balance. Recomputes `payment_status` from the ledger — it is never typed.
*Roles*: Super, Store Manager, Finance.

### Issue a refund
`issue_refund` action: amount, reason. Enforces `Σ refunds ≤ captured` under a row lock **and** a database constraint (INV-004). **Never restocks automatically** — restocking is a separate explicit decision (FR-028).
*Roles*: Super, Finance.

### Moderate a review
Approve or reject; approval recomputes the product's aggregate rating and count. Aggregates are never hand-edited (FR-094).
*Roles*: Super, Store Manager, Catalogue Manager, Customer Service, Content Manager.

### Edit storefront content
Site settings, home sections, banners, FAQs, static pages, navigation. Changes are audited. **Content editing cannot alter layout or component structure** (FR-099) — the preservation boundary still applies.
*Roles*: Super, Store Manager, Content Manager.

---

## 3. Prohibited for everyone — including superusers

| Action | Why |
|---|---|
| Edit or delete an `AuditLog` | INV-013 — no code path exists |
| Edit or delete a `StockMovement` | Ledger integrity |
| Edit or delete a `PaymentEvent` | Payment integrity |
| Edit or delete an `OrderEvent` | History integrity |
| Edit an `OrderLine` price, quantity or snapshot | INV-003 |
| Edit `Order` totals directly | FR-105 |
| Delete an `Order` | Cancel instead |
| Delete a product referenced by an order | Archive instead (FR-014) |
| Set stock so `on_hand < reserved` | INV-001 |
| Refund beyond captured | INV-004 |
| Import orders, payments or refunds | Would bypass every invariant |
| Run `seed_demo` in production | FR-122 |

These are enforced by the **absence of an implementation**, not by a permission flag that could be granted.

---

## 4. Dashboard

11 widgets (`admin-model-matrix.md` §2), each date-bounded or `LIMIT`-capped and index-backed, with a total query budget asserted by `test_dashboard_query_budget`. A metric that cannot be computed exactly is **not shown** — a misleading number is worse than an absent one (FR-102).

---

## 5. Guarantees to staff

1. An action that succeeds has fully succeeded — no partial writes.
2. An action that fails changes nothing.
3. Concurrent edits produce one winner; the loser sees the current state, not a silent overwrite.
4. Every change is attributable.
5. Refused actions explain **why** and what is allowed instead.
6. Financial totals always reconcile with the payment ledger.
