# Contract: Checkout Information, Order Review, and Enquiry

**Feature**: `001-premium-storefront-experience`
**Contract ID**: `C-CHECKOUT`
**Boundary**: Feature 001 terminates at a **validated order-review state**. It creates no order,
takes no payment, and stores no payment credential.

## The hard prohibitions

These are structural, not stylistic. Each is enforced by a test that fails the build.

| Prohibited | Enforcement |
| --- | --- |
| Any field collecting a card number, expiry, security code, PIN, or payment credential | Form-field audit across every form in the project asserts zero matches; SC-022, SC-039 |
| A payment step, payment-method selector, or saved-card option | Route and template audit; FR-105 |
| A simulated payment outcome | No payment code path exists to simulate |
| A control claiming to place an order, complete a purchase, or confirm payment | Visible-copy audit over rendered pages; FR-108, SC-038 |
| Creating an order record or an identifier presented as an order number | Stored-state inspection after a full checkout journey; FR-109, SC-044 |
| A persistent customer account | No account model, no auth routes |

## Checkout information state

```
session["zakey_checkout"] = {"v": 1, "fields": {...}, "validated": <bool>}
```

Collected fields — contact and delivery only:

```
full_name          required, 1..120
email              required, RFC-validated
phone              optional, permissive international format
address_line1      required, 1..160
address_line2      optional, 0..160
city               required, 1..80
region             optional, 0..80
postal_code        optional, 0..24
country            required, choice from a verified list
delivery_notes     optional, 0..500
```

No shipping-method selector and no tax field exist, because no verified delivery or tax fact exists
(RD-7, §9 of the specification).

## Step flow

```
/cart/  --(POST proceed)-->  /checkout/information/  --(POST, server-validated)-->  /checkout/review/
                                       ^                                                   |
                                       +---------------- (edit information) ---------------+
/cart/  <--------------------------- (edit cart) --------------------------------------- /checkout/review/
```

- Progress is shown and is **exposed assistively**, not by visual styling alone (A-20).
- Backward navigation preserves every entered value (FR-103, US6.4).
- `/checkout/review/` is reachable **only** when `validated is True` **and** the cart is non-empty.
  Direct navigation otherwise redirects to the appropriate earlier step with an explanation — the
  review state can never be reached by URL guessing (FR-104, SC-037).
- Entering checkout with an empty cart returns the visitor to the cart's empty state (edge case).

## Validation contract

```
ValidationResult
  valid:        bool
  field_errors: Mapping[str, Sequence[ErrorDetail]]
  form_errors:  Sequence[ErrorDetail]
  first_invalid_field: str | None

ErrorDetail { code: str, message_key: str, params: Mapping }
```

- **Server-side validation is the enforcement boundary**; client-side is assistance only (FR-055).
- Field-level messages are programmatically associated with their field; the field is marked
  invalid; a form-level summary appears when more than one field fails (FR-056, A-8).
- On failure, focus moves to `first_invalid_field` and **all entered values are preserved**
  (FR-057).
- An invalid email is reported against the email field specifically, not as a whole-form rejection
  (US6.3).

## Order-review generation

```
OrderReview
  lines:            Sequence[ResolvedLine]   # from catalog.resolve_lines — never re-derived
  totals:           Totals                   # from the same call; None when not computable
  information:      Mapping[str, str]        # validated values, escaped on render
  computable:       bool
  disclosure_key:   str                      # "no order placed, no payment taken"
  actions:          [EDIT_CART, EDIT_INFORMATION, SEND_ENQUIRY]
```

- Totals are produced **only** by `catalog.resolve_lines(...)` at render time (FR-099). Nothing is
  read back from the session, so a tampered or stale session cannot influence a figure.
- When any line is price-on-request, `computable` is `False`, **no monetary total is rendered**, and
  the price-on-request statement appears instead (FR-098, FR-106, SC-040).
- The review page states plainly that **no order has been placed and no payment has been taken**
  (FR-107). This is required copy, not optional reassurance.
- `actions` contains exactly three members. There is no fourth. A "Place Order" control does not
  exist anywhere in the codebase (FR-108).

**Stale-cart guard.** The review renders a cart digest. If the cart changes or empties between
information submission and review render, the digest mismatches, the review **refuses to present
stale contents**, and the visitor returns to the cart with an explanation (FR-110, edge case
"cart emptied in another tab").

**Session expiry.** If the session expires mid-checkout, the visitor is told plainly and returned to
a valid state. No partial artifact is created (edge case).

## Enquiry submission — the only terminal state-changing action

```
POST /enquiry/
  contact fields (as above, re-validated server-side)
  message: optional, 0..2000
  source:  PRODUCT | CART | REVIEW | CONTACT
```

Behaviour, in strict order:

1. Re-validate everything server-side. Client state is never trusted.
2. Re-resolve product lines through `C-CATALOG`. Line identity and any prices come from the
   provider, never from the request body — a forged price in a POST has nowhere to land.
3. Persist an `Enquiry` row (R-016) inside a transaction.
4. **Only after the write commits**, redirect to a confirmation.

If the write fails: an honest failure state, entered values preserved, retry offered, **no
confirmation shown** (FR-060, FR-052, SC-023 verified by fault injection).

Confirmation copy MUST be worded as *an enquiry has been received*. It MUST NOT describe an order as
placed, paid, reserved, or shipped, and MUST NOT promise a reply time, price, availability, or
delivery unless verified (FR-052, FR-063).

Double-submission is prevented by POST/Redirect/GET plus a per-form idempotency token; exactly one
row is created (edge case).

## Enquiry-only products

Because all 21 verified products are `PRICE_ON_REQUEST`, the enquiry path is the primary
conversion route in Feature 001:

- Product page: "Request price" alongside "Add to cart".
- Cart and review: enquiry offered whenever `computable` is `False` (FR-098).
- Wishlist: whole shortlist convertible to one enquiry (FR-044, FR-048).

When Feature 002 supplies verified prices, `computable` becomes `True`, totals appear, and the
enquiry route remains for genuinely unpriced items. Both paths are implemented and tested now, so
no redesign is needed then.

## Feature 002 handover

Feature 002 attaches order creation **behind** the review state: it adds a payment step and an
order-creation action after review, converting `OrderReview` into an order. Everything above the
seam — cart, resolution, validation, review rendering — is reused unchanged.
