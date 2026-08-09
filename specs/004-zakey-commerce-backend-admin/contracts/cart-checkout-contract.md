# Contract: Cart and Checkout

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-030 – FR-039, FR-060 – FR-069, FR-132, FR-134.

Governs the transition from `localStorage` prototype state to server-owned commerce state.

---

## 1. Non-negotiable principle

> **The server never trusts the browser for anything monetary.**

Requests carry **identifiers and intent only** — variant id, quantity, coupon code, shipping method code, address fields, payment method code. They never carry price, subtotal, VAT, discount, shipping cost or total. Any such field present in a request is **ignored, not validated** (FR-034).

---

## 2. Endpoints

All POST, all CSRF-protected, all returning a redirect (PRG) or a rendered fragment. No JSON API is introduced (`research.md` §6).

| Endpoint | Payload | Rules |
|---|---|---|
| `POST /cart/add/` | `variant_id`, `quantity` | variant published & purchasable; 1 ≤ qty ≤ 9; ≤ available |
| `POST /cart/update/` | `line_id`, `quantity` | line belongs to this cart; same bounds |
| `POST /cart/remove/` | `line_id` | ownership checked |
| `POST /cart/coupon/` | `code` | uppercased; full eligibility; existing Arabic messages |
| `POST /cart/coupon/remove/` | — | — |
| `POST /wishlist/toggle/` | `product_id` | ownership checked |
| `POST /checkout/shipping/` | 12 fields (§4) | full server validation |
| `POST /checkout/payment/` | `payment_method` | must be active |
| `POST /checkout/place/` | `idempotency_key` | atomic order creation |

Cart identity: authenticated → `customer`; anonymous → `session_key`. Every mutation re-derives the cart from the request; a client-supplied cart id is never accepted.

---

## 3. Cart line identity ★

```
UniqueConstraint(cart, variant)
```

Add, update **and** remove all key on `(cart, variant)`.

> This deliberately fixes the prototype defect: `store.js:24-26` adds by `(productId, finishId)` but `store.js:34,41` updates and removes by `productId` alone, so two finishes of the same product cannot be managed independently (`frontend-contract.md` §3). T-0703 covers it with an explicit test.

---

## 4. Checkout validation

Server-side, reproducing the client rules and **the exact Arabic messages** (`checkout.js:145-158`, `dom.js:31-39`):

| Field | Rule | Message |
|---|---|---|
| `fullName` | ≥2 chars, contains an Arabic letter | اكتب الاسم بالكامل بالعربية. |
| `email` | valid format | اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com. |
| `mobile` | `^01[0125]\d{8}$` after normalisation | اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا. |
| `governorate` | required, active | اختر المحافظة. |
| `city` | ≥2 chars | اكتب اسم المدينة أو المركز. |
| `areaKey` | optional; must belong to the governorate | — |
| `street` | ≥4 chars | اكتب اسم الشارع والعنوان التفصيلي. |
| `building` | required | اكتب رقم المبنى. |
| `landmark` | optional | — |
| `shippingMethod` | required, eligible for this address and cart | اختر طريقة الشحن. |
| `installation` | only if governorate eligible **and** every line supports it | — |
| `acknowledgement` | required → **terms acceptance** (FR-063) | أكد فهمك أن هذه واجهة تجريبية. → updated terms wording |

Mobile normalisation: strip non-digits except `+`; `+20…`→`0…`; `20…` (12 chars)→`0…`; fold Arabic-Indic digits; then match.

Errors render into the existing `.field-error` elements and `[data-error-summary]` list — no new markup, no new styling.

---

## 5. Totals

```
line_total   = quantize(variant.price × quantity)
subtotal     = Σ line_total
discount     = coupon rules (capped)
discounted   = subtotal − discount
shipping     = 0 if discounted ≥ threshold and method is free-eligible, else zone rate   ← NEW ROW
installation = fee if requested and eligible, else 0                                      ← NEW ROW
grand_total  = discounted + shipping + installation
vat          = quantize(grand_total × 14 ÷ 114)     ← extraction, informational
```

VAT is **extracted, never added** (INV-011). The two new rows are the approved deltas in `frontend-preservation-boundary.md` §4.

---

## 6. Order creation

One transaction (`inventory-integrity.md` §2.2): revalidate cart → lock stock rows ordered by `variant_id` → lock coupon → recompute all totals from locked rows → create order, lines, address, event → reserve stock → redeem coupon → mark cart converted.

Idempotency: `Order.idempotency_key` unique; the handler inserts and, on `IntegrityError`, returns the existing order. A double-click, a refresh and a replayed POST all yield exactly one order (INV-002).

Failure rolls back completely — **the cart survives intact**, which matters because a customer who loses their cart at checkout does not come back.

---

## 7. `localStorage` migration

`zakey:prototype:v1` holds `{version, cart, wishlist, account}` (`storage-adapter.js:1`).

On first authenticated page load after integration, a one-time adapter reads that key, POSTs its lines to the server cart (validating each), merges the wishlist, then clears it. Products that no longer exist are dropped silently; the customer is not shown an error for demo data. The adapter runs once, is idempotent, and after Phase 16 the browser holds no commerce state at all (FR-132).

---

## 8. Guarantees

1. Displayed totals always equal server-computed totals.
2. Stock is never oversold (`inventory-integrity.md`).
3. A replay never creates a second order.
4. A failed checkout never leaves a partial order.
5. A customer only ever touches their own cart, wishlist and orders.
6. Every mutation is POST + CSRF (FR-039).
7. Pages remain usable without JavaScript (FR-136).
