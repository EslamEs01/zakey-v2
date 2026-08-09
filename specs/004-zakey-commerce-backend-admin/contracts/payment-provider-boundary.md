# Contract: Payment Provider Boundary

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-070 – FR-079, INV-004.

---

## 1. Statement of fact

**No payment provider integration exists in this repository.** Verified: no SDK, no credential, no endpoint, no webhook handler, no provider reference anywhere in the working tree. The 6 payment options are display labels, each carrying an explicit Arabic notice that no provider is connected (`frontend-contract.md` §2).

Nothing in this feature may claim otherwise. A task, comment, log line or report asserting a live gateway is a defect.

---

## 2. Classification of the 6 options

| Code | Label | Class | Launch behaviour |
|---|---|---|---|
| `payment-cod` | الدفع عند الاستلام | **Operational** | Order placed, collected on delivery, staff record receipt |
| `payment-instapay` | InstaPay | **Manual/offline** | Customer transfers out-of-band; staff record the payment against the order |
| `payment-vodafone-cash` | Vodafone Cash | **Manual/offline** | Same |
| `payment-etisalat-cash` | e& Cash | **Manual/offline** | Same |
| `payment-cashu` | CashU | **Deferred** | Rendered as coming-soon |
| `payment-installments` | تقسيط ببطاقة بنكية مصرية | **Deferred** | Rendered as coming-soon |

All 6 keep rendering exactly as today. Marking one unavailable **must not change the layout** (FR-072) — the option renders in its existing slot with a disabled state, not removed.

---

## 3. The boundary

```
orders.services  ──►  payments.services.PaymentGateway  (abstract)
                                  │
                ┌─────────────────┼─────────────────┐
          ManualGateway      CODGateway      <FutureProvider>
```

**Interface**: `create_payment(order, amount, method)` · `capture(payment)` · `cancel(payment)` · `refund(payment, amount, reason)` · `handle_callback(payload, signature)`.

`orders` never imports a concrete gateway. Adding a real provider is one new class plus one settings block — no change to order logic, no migration to the order model.

---

## 4. Requirements for a future real integration

A provider task may only begin when **all** of these hold, and it is a separately approved increment (FR-079):

1. Credentials exist in the environment (never in code, fixtures or the admin).
2. Official provider documentation is available.
3. Provider **test mode** is confirmed working.
4. The user has explicitly approved that increment.

It must then implement: signature verification; idempotent callbacks keyed on a unique `provider_event_id`; a state machine matching `payment-state-machine.md`; refund support; reconciliation; and full audit. It must **not** store card data.

---

## 5. Data rules

| Rule | |
|---|---|
| Card number, CVV, PAN | **Never** stored, logged or transmitted to this system (FR-077) |
| Provider payloads | Only a `payload_digest` hash is stored — never the raw body |
| Credentials | Environment only (FR-078) |
| Logs | Redact every provider identifier and customer contact detail |
| PCI scope | Minimised by design: this system never receives card data, so a hosted/redirect flow is mandatory for any future gateway |

---

## 6. Idempotency and replay

`PaymentEvent.provider_event_id` is **unique**. A replayed callback violates the constraint and is swallowed as a no-op rather than double-crediting an order. Callbacks for unknown, cancelled or already-terminal orders are recorded and ignored, never applied. Handlers are pure functions of `(order, event)` so re-delivery converges to the same state.

---

## 7. Reconciliation

`python manage.py reconcile_payments` reports — without mutating — orders paid with no capture, captures with no paid order, refunds exceeding captures, orphan payments, and status divergence. Non-zero exit on divergence so it can be scheduled as a check.

---

## 8. Verification

`tests/integration/test_payments.py` and `tests/concurrency/test_payment_races.py` cover: state transitions, refund limits under concurrency, duplicate `provider_event_id` yielding one event, callbacks for cancelled orders being ignored, and `tests/security/test_no_card_data.py` asserting no card-shaped data is persisted or logged anywhere.
