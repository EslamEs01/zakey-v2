# Order State Machine

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-068, FR-069, INV-006.

Three independent axes. Keeping them separate avoids the combinatorial mess of one status field trying to express payment and delivery at once.

---

## 1. Order status (lifecycle)

| State | Meaning |
|---|---|
| `pending` | Created, stock reserved, awaiting payment or staff confirmation |
| `confirmed` | Accepted by staff / payment secured; ready to fulfil |
| `processing` | Being picked and packed |
| `shipped` | Handed to courier |
| `delivered` | Received by customer — **terminal (success)** |
| `cancelled` | Cancelled before delivery — **terminal** |
| `refunded` | Fully refunded after delivery — **terminal** |

### Allowed transitions

| From | Allowed to | Who |
|---|---|---|
| `pending` | `confirmed`, `cancelled` | Staff, system (payment), customer (cancel only) |
| `confirmed` | `processing`, `cancelled` | Staff |
| `processing` | `shipped`, `cancelled` | Staff |
| `shipped` | `delivered`, `cancelled` | Staff |
| `delivered` | `refunded` | Finance / Store Manager |
| `cancelled` | — | terminal |
| `refunded` | — | terminal |

**Every other pair is rejected**, including all backward moves (`shipped → pending`), all skips (`pending → delivered`), and every transition out of a terminal state. Rejection raises a domain error naming the current state and the allowed set; it is never silently ignored.

```
pending ──► confirmed ──► processing ──► shipped ──► delivered ──► refunded
   │            │             │             │
   └────────────┴─────────────┴─────────────┴──► cancelled
```

### Side effects (all inside the transition transaction)

| Transition | Effect |
|---|---|
| → `confirmed` | Reservation stays; `OrderEvent` written |
| → `processing` | Reservation → consumed; `fulfill` movement deducts `on_hand` |
| → `shipped` | Tracking recorded; customer notified |
| → `delivered` | Enables review verified-purchase flag (FR-092) |
| → `cancelled` | Reservation released (`release` movement); coupon redemption reversed; payment cancelled if uncaptured |
| → `refunded` | Requires a completed `Refund` covering the captured amount; **stock is NOT auto-restocked** — staff decide (FR-028) |

---

## 2. Payment status (derived, never hand-set)

`unpaid` → `partially_paid` → `paid` → `partially_refunded` → `refunded`; plus `failed` and `cancelled`.

Recomputed from `Payment` rows after every payment or refund event. Staff cannot type it. Divergence between this and the `Payment` ledger is exactly what the reconciliation command reports (FR-076).

---

## 3. Fulfilment status

`unfulfilled` → `partially_fulfilled` → `fulfilled`, plus `returned`. Driven by shipment records, not typed by hand.

---

## 4. Cancellation rules

- Customer may cancel only while `pending` or `confirmed`, and only their own order (INV-010).
- Staff may cancel up to `shipped`.
- Cancellation after capture requires a refund decision; it cannot silently strand money.
- Cancelling always releases reservations in the same transaction — a failure to release must roll back the cancellation.

## 5. Concurrency

Every transition takes `SELECT … FOR UPDATE` on the order row, re-reads the current status inside the lock, and re-validates the edge. Two staff members clicking different transitions simultaneously produce exactly one winner; the loser gets a stale-state error naming the new current state. Covered by `test_order_transition_concurrency` on PostgreSQL (NFR-005).

## 6. Audit

Every transition writes an `OrderEvent` (actor, from, to, timestamp, request id) and an `AuditLog` row. A transition that fails to write its event must roll back the transition (FR-069, FR-113).

## 7. Test obligation

`test-strategy.md` requires a parametrised test over the **full Cartesian product** of states — every allowed edge succeeds and every disallowed edge raises — satisfying SC-005 at 100% transition coverage.
