# Payment State Machine and Provider Boundary

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-070 – FR-079, INV-004.

---

## 1. Honest starting position

The repository contains **no payment provider integration of any kind** — no SDK, no credential, no endpoint, no webhook handler, no provider reference. The 6 payment options in `paymentOptions` are display labels, each carrying an explicit Arabic notice that no provider is connected (`frontend-contract.md` §2).

Therefore this feature ships:

| Category | Methods | Status at launch |
|---|---|---|
| **Operational** | `payment-cod` (cash on delivery) | Fully functional |
| **Manual/offline** | `payment-instapay`, `payment-vodafone-cash`, `payment-etisalat-cash` | Staff record receipt manually against the order |
| **Deferred** | `payment-cashu`, `payment-installments` | Rendered as coming-soon; no integration claimed |

Nothing here claims a live gateway. Any statement to the contrary in a task or report is a defect.

---

## 2. Payment states

| State | Meaning |
|---|---|
| `pending` | Attempt created, no money moved |
| `authorised` | Funds held, not captured (gateway only, unused at launch) |
| `captured` | Money received |
| `failed` | Attempt failed — terminal |
| `cancelled` | Attempt abandoned — terminal |
| `refunded` | Fully refunded — terminal |
| `partially_refunded` | Some amount returned |

### Allowed transitions

| From | Allowed to |
|---|---|
| `pending` | `authorised`, `captured`, `failed`, `cancelled` |
| `authorised` | `captured`, `cancelled`, `failed` |
| `captured` | `partially_refunded`, `refunded` |
| `partially_refunded` | `partially_refunded`, `refunded` |
| `failed` / `cancelled` / `refunded` | — terminal |

```
pending ──► authorised ──► captured ──► partially_refunded ──► refunded
   │            │              │                │
   └────────────┴──► failed    └────────────────┴──► refunded
   └──► cancelled
```

Money can never move backwards into `pending`. A `captured` payment can never become `failed`.

---

## 3. Refund rules

- **INV-004**: `Σ completed refunds ≤ captured amount`, per payment.
- Enforced twice: a `CheckConstraint(amount > 0)` at the database plus a service check performed **inside** a `SELECT … FOR UPDATE` on the payment row, so two concurrent refund requests cannot both pass.
- A refund against a payment that is not `captured` or `partially_refunded` is rejected.
- Refunds do not restock automatically — staff decide (FR-028).
- Every refund writes an `AuditLog` with actor and reason.

---

## 4. Idempotency and webhook safety

Even though no provider is connected yet, the boundary is built correctly now so integration is a small, safe increment later:

1. `PaymentEvent.provider_event_id` is **unique** — a replayed callback violates the constraint and is swallowed as a no-op rather than double-crediting.
2. Signature verification is mandatory before any state change; unverified payloads are logged and dropped.
3. Callbacks for unknown, cancelled or already-terminal orders are recorded and ignored, never applied.
4. Handlers are pure functions of `(order, event)` so re-delivery converges to the same state.
5. Only a `payload_digest` is stored — never a raw payload, never card data (FR-077).

---

## 5. Provider boundary

```
orders/services  ─calls─►  payments.services.PaymentGateway (ABC)
                                    │
                    ┌───────────────┼───────────────┐
             ManualGateway     CODGateway    <FutureProvider>
             (staff records)  (on delivery)  (separate task, needs credentials)
```

The abstract interface is `create_payment`, `capture`, `cancel`, `refund`, `handle_callback`. Orders never import a concrete provider. Adding a real gateway means adding one class and one settings block — no change to order logic.

**A real provider task may only start when**: credentials exist in the environment, official provider documentation is available, provider test mode is confirmed working, and the user has explicitly approved that increment (FR-079).

---

## 6. Reconciliation

`python manage.py reconcile_payments [--since]` reports, without mutating anything:

- orders marked paid with no captured payment;
- captured payments whose order is unpaid;
- refunds exceeding captures;
- payments with no order;
- orders whose `payment_status` disagrees with the ledger.

Exit code is non-zero when divergence is found, so it can run as a scheduled check.
