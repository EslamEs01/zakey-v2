# Inventory Integrity and Transaction Safety

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-020 – FR-029, FR-061, FR-064, FR-083, INV-001, INV-002, INV-005.

---

## 1. The invariant

```
available = on_hand − reserved        and        available ≥ 0
```

Expressed as a database `CheckConstraint(reserved <= on_hand)` on `StockItem`. This matters: it means overselling is impossible **even if every line of application code is wrong**. Application logic is the first defence; the constraint is the one that cannot be bypassed by a bug, a shell session, a data import or an admin action.

Inventory integrity never depends on JavaScript, admin form validation, or a `full_clean()` call somebody forgot (FR-029).

---

## 2. Sensitive workflow ledger

Each workflow below is specified as: transaction boundary → locked rows → invariant → failure → retry → idempotency → audit.

### 2.1 Add to cart

- **Boundary**: single `atomic()`
- **Locks**: none (advisory read of `available` only)
- **Invariant**: requested quantity ≤ available, 1 ≤ quantity ≤ 9
- **Failure**: reject with Arabic message; cart unchanged
- **Retry**: safe, naturally idempotent per `(cart, variant)` upsert
- **Idempotency**: `UniqueConstraint(cart, variant)` (FR-030)
- **Audit**: none (not a financial event)

> Deliberately *not* locked. Stock is verified for real at checkout. Locking on every add-to-cart would serialise browsing for no benefit — a customer holding a cart has no claim on stock.

### 2.2 Order creation ← **the critical one**

- **Boundary**: one `atomic()` wrapping validation, reservation, coupon consumption, order write, event write (FR-061)
- **Locks**, always acquired in this order to prevent deadlock:
  1. `StockItem` rows for every line, `select_for_update()`, **ordered by `variant_id` ascending**
  2. `Coupon` row, `select_for_update()`, if one is applied
- **Invariants**: `reserved + qty ≤ on_hand` per line; `coupon.times_used < usage_limit`; totals recomputed server-side from the locked variants (FR-034)
- **Failure**: whole transaction rolls back — no order, no reservation, no redemption, no partial write; the cart survives intact
- **Retry**: safe — replay returns the existing order
- **Idempotency**: `Order.idempotency_key` unique. The handler tries the insert; on `IntegrityError` it selects and returns the existing order (INV-002, FR-064)
- **Audit**: `OrderEvent(created)` + `StockMovement(reserve)` per line + `CouponRedemption`

**Deterministic lock ordering is the whole trick.** Two carts holding variants {A,B} and {B,A} would deadlock without it; sorting by `variant_id` means both take A then B.

### 2.3 Stock adjustment (admin)

- **Boundary**: `atomic()`
- **Locks**: `StockItem` `select_for_update()`
- **Invariant**: resulting `on_hand ≥ reserved`; a reason is mandatory
- **Failure**: reject, naming how many units are currently reserved
- **Idempotency**: none — adjustments are deliberate discrete events
- **Audit**: `StockMovement` + `AuditLog` with actor

### 2.4 Fulfilment

- **Locks**: `StockItem` + `Order`
- **Effect**: `on_hand −= qty`, `reserved −= qty`, reservation → `consumed`
- **Invariant**: reservation must be `active` and belong to this order
- **Audit**: `StockMovement(fulfill)`

### 2.5 Cancellation / expiry

- **Locks**: `StockItem` + `Order`
- **Effect**: `reserved −= qty`, reservation → `released`/`expired`
- **Invariant**: `reserved ≥ 0`; releasing twice is a no-op guarded by reservation state
- **Idempotency**: state check makes double-release harmless
- **Audit**: `StockMovement(release)`

### 2.6 Coupon redemption

- **Locks**: `Coupon` `select_for_update()` inside the order transaction
- **Invariant**: `times_used < usage_limit`; per-customer count < `per_customer_limit`
- **Failure**: whole order fails; customer sees the existing Arabic rejection message
- **Idempotency**: `UniqueConstraint(coupon, order)`
- **Audit**: `CouponRedemption` row

### 2.7 Refund

See `payment-state-machine.md` §3. Locked on the `Payment` row; `Σ refunds ≤ captured` re-checked inside the lock.

---

## 3. Reservation lifecycle

```
        checkout
           │
           ▼
       ┌────────┐  fulfil   ┌──────────┐
       │ active │──────────►│ consumed │
       └───┬────┘           └──────────┘
           │ cancel / payment fail
           ▼
       ┌──────────┐      TTL      ┌─────────┐
       │ released │◄──────────────│ expired │
       └──────────┘               └─────────┘
```

TTL is `SiteSetting.reservation_ttl_minutes` (default 60). `python manage.py release_expired_reservations` is idempotent, batched, locks each stock item, and reports released counts. Running it twice releases nothing the second time.

---

## 4. Race conditions and how each is closed

| Race | Defence |
|---|---|
| Two checkouts, last unit | `select_for_update` on `StockItem` + `CheckConstraint(reserved <= on_hand)` |
| Double-click checkout | Unique `idempotency_key` |
| Replayed checkout POST | Same |
| Two redemptions of the last coupon use | `select_for_update` on `Coupon` + check constraint |
| Deadlock across multi-line carts | Deterministic lock order by `variant_id` |
| Duplicate payment callback | Unique `provider_event_id` |
| Concurrent refunds exceeding capture | Locked re-check + constraint |
| Two staff transitioning one order | `select_for_update` on `Order`, re-validate inside lock |
| Order number collision | Unique constraint + retry on `IntegrityError` |
| Stale cart price | Recompute from locked variant at order time |
| Admin adjusting stock during checkout | Both paths lock the same `StockItem` |

---

## 5. Verification obligation

Every row in §4 has a named PostgreSQL test in `test-strategy.md` §4 using real threads or `TransactionTestCase`, asserting both the success count and that `available` never went negative. **SQLite passes are not accepted as evidence** (FR-002, NFR-005) — SQLite does not implement `SELECT … FOR UPDATE` and would give a false green.

## 6. Recovery

- `release_expired_reservations` — sweeps stranded reservations
- `reconcile_payments` — reports payment/order divergence
- `verify_stock_integrity` — recomputes `reserved` from active reservations and reports drift **without mutating**; any drift is a bug to investigate, never silently patched
