# Contract: Session State — Cart and Wishlist Mutations

**Feature**: `001-premium-storefront-experience`
**Contract ID**: `C-SESSION`
**Stability**: Session *shape* is versioned and may change in Feature 002; the *service interface*
is stable.

## Governing principle

**The browser is never the authority for price, product identity, totals, or validation.** The
client holds only an opaque `HttpOnly` session cookie. The session stores identifiers and
quantities. Everything else — names, images, prices, totals, availability — is resolved server-side
on every render through `C-CATALOG`.

## Stored shape (server-side only)

```
session["zakey_cart"]     = {"v": 1, "lines": [{"sku": <str>, "qty": <int>}]}
session["zakey_wishlist"] = {"v": 1, "skus": [<str>, ...]}
```

**Prohibited in the session, without exception:** price, currency, line total, subtotal, grand
total, product display name, product image path, availability text, or any rendered string.
Storing any of these creates a second source of truth for money and is a contract violation.

`v` is the schema version. On read, a mismatched `v` causes the structure to be **discarded**, not
migrated blindly — a stale shape can never be reinterpreted as a valid one.

## Service interface

```
CartService(session, catalog)
  add(sku: str, qty: int)         -> MutationResult
  update(sku: str, qty: int)      -> MutationResult
  remove(sku: str)                -> MutationResult
  clear()                         -> MutationResult
  read()                          -> CartView       # resolved, priced, totalled
  line_count()                    -> int

WishlistService(session, catalog)
  toggle(sku: str)                -> MutationResult
  remove(sku: str)                -> MutationResult
  move_to_cart(sku: str)          -> MutationResult
  read()                          -> WishlistView
  count()                         -> int

MutationResult
  ok:            bool
  code:          MutationCode
  message_key:   str              # i18n key; never a raw rendered string
  cart_count:    int
  wishlist_count: int
```

`MutationCode` ∈ `OK | UNKNOWN_SKU | INVALID_QTY | EMPTY | NOOP`.

`read()` returns a **fully resolved** view built by calling `catalog.resolve_lines(...)`. Totals
come from there and nowhere else (FR-099).

## Server-side validation rules

| Rule | Behaviour | Requirement |
| --- | --- | --- |
| `qty` must be an integer in **1–99** | Out-of-range or non-numeric ⇒ `INVALID_QTY`, field-level message, line unchanged, **not** silently removed | FR-096, edge case |
| `qty = 0` submitted to `update` | Rejected as `INVALID_QTY`. Removal is an explicit `remove` action | edge case |
| Unknown or withdrawn `sku` on **write** | `UNKNOWN_SKU`, no session change, honest error | FR-101 |
| Unknown or withdrawn `sku` on **read** | Dropped **silently**, counts corrected, no error shown | FR-101, FR-047 |
| Duplicate `add` of an existing sku | Quantities sum, then clamp to 99 | FR-093 |
| Cart line cap | Maximum 50 distinct lines; further adds return `INVALID_QTY` with an honest message | denial-of-service guard |
| Wishlist cap | Maximum 100 skus | denial-of-service guard |

All validation is server-side. Client-side validation is assistance only (FR-055, NFR-040).

## HTTP behaviour

- Every mutation is **POST only**. `GET` on a mutation route returns **405**. A cart cannot be
  changed by a link, a prefetch, or a crawler.
- Every mutation requires a valid **CSRF token** (NFR-039).
- Every mutation responds **303 See Other** to a canonical GET (POST/Redirect/GET), so reload and
  back never re-submit (edge case: "form submitted twice rapidly ⇒ exactly one operation occurs").
- With JavaScript, the same endpoint accepts `Accept: application/json` and returns
  `MutationResult` as JSON for in-place updates. **The endpoint, validation, and result are
  identical either way** — the JSON path is a rendering optimisation, never a second code path with
  its own rules (FR-089, R-014).

## Persistence guarantee

Cart and wishlist survive navigation and full page reload for the life of the session, because
state lives in the server-side session store (R-004), not in the page. Verified by SC-035 and
SC-036: at least five page transitions plus a reload, with lines and quantities identical.

Session cookie: `HttpOnly`, `SameSite=Lax`, `Secure` in production, no client-readable payload.
The session key is **cycled on privilege-relevant transitions** to prevent fixation (NFR-039).

## Language rules

No cart or wishlist surface may describe its contents as an order, a reservation, a held item, a
payment, or a completed purchase (FR-046, FR-102, CI-17, SC-038). `message_key` values are i18n
keys resolved through the translation layer, keeping copy out of the service layer and localisation
possible later (FR-078).

## Feature 002 migration path

The session cart becomes the **input** to real order creation. `v` is incremented when the shape
changes; live sessions with an older `v` are discarded rather than mis-read. `CartService.read()`
already returns fully resolved, server-computed totals, so order creation consumes the same
resolution path that the cart displays — no divergence is possible.
