# Contract: HTTP Behaviour, Errors, and Progressive Enhancement

**Feature**: `001-premium-storefront-experience`
**Contract ID**: `C-HTTP`

## Method and status contract

| Route class | Methods | Notes |
| --- | --- | --- |
| Content pages (home, listing, category, collection, product, search, informational) | `GET`, `HEAD` | Safe, cacheable, no side effects |
| Cart / wishlist mutations | `POST` only | `GET` ⇒ **405**; a link, prefetch, or crawler can never mutate state |
| Checkout information | `GET` (render), `POST` (submit) | |
| Checkout review | `GET` only | Reachable only when validated and cart non-empty |
| Enquiry | `POST` only | The single terminal state-changing action |

| Situation | Status | Response |
| --- | --- | --- |
| Unknown product / category / collection slug | **404** | Custom 404, working navigation, no internal detail (FR-084, FR-086) |
| Page number beyond last | **302** | Redirect to the last valid page — never an unhandled error (FR-088) |
| Empty or whitespace-only search | **200** | Renders the range; **does not** present a results page implying a search occurred (FR-027) |
| Mutation with unknown sku | **400** or redirect + honest message | No session change |
| Mutation with invalid quantity | **400** or redirect + field error | Line unchanged, not removed |
| Checkout review without validation | **302** | To the information step, with an explanation |
| Checkout from empty cart | **302** | To the cart's empty state |
| Cart changed mid-checkout (digest mismatch) | **302** | To the cart, with an explanation (FR-110) |
| Session expired mid-checkout | **302** | To a valid state, plainly explained; no partial artifact |
| CSRF failure | **403** | Custom template, no stack trace |
| Unhandled server error | **500** | Custom 500, working navigation, no stack trace, no internal detail (FR-085) |

**No status code is ever faked.** A failed operation never returns a success page, and a success
page never renders without its underlying operation having succeeded (FR-059, SC-023).

## Redirect safety

Any `next`/`return_to` parameter is validated with an **allow-list of named routes**, not a URL
parser. A value that does not resolve to a known route name is discarded and the default is used.
Open redirects are therefore not possible, because an arbitrary URL has no way to be expressed.

## Content negotiation — one code path, two renderings

Mutation endpoints accept both:

- **Default (no JavaScript):** form POST → validate → mutate → **303** to a canonical GET.
- **Enhanced:** `Accept: application/json` → identical validation and mutation → `MutationResult`
  JSON.

**Both paths execute the same service call with the same validation.** The JSON path is a rendering
choice, never a second set of rules. This is what makes FR-089 achievable without maintaining two
divergent implementations (Constitution IV.4).

## Progressive-enhancement matrix

| Capability | Without JavaScript | With JavaScript |
| --- | --- | --- |
| Browse, category, collection, product | Full | Full |
| Filter / sort / paginate | Form submit + links; state in query string | Same URLs, no full reload |
| Search | Form GET | Same, plus focus management |
| Add / update / remove cart | Form POST → 303 | In-place count and line update |
| Wishlist toggle | Form POST → 303 | In-place toggle + count |
| Checkout → review | Full | Same, plus inline validation assistance |
| Enquiry submission | Full | Same, plus busy state |
| Gallery | All images rendered, navigable as links/anchors | Thumbnail switching, keyboard arrows |
| Mobile navigation | `<details>`-based disclosure, fully operable | Drawer with focus trap and Escape |
| Filter panel (narrow) | Inline expanded form | Drawer with focus trap and Escape |
| Toasts | Not rendered — the redirect target states the outcome | Transient, assistively announced |

**Rule:** a control that requires scripting is **rendered by scripting**. Nothing inert ever appears
(FR-089, FR-053, Constitution VI.2).

## Error-state rendering

Every error state must: explain what happened without internal detail; preserve the visitor's input;
offer a next action (FR-081, FR-060).

| Level | Rendering |
| --- | --- |
| Field | Message adjacent to the field, `aria-describedby`-linked, field marked invalid (A-8) |
| Form | Summary above the form when more than one field failed; focus to first invalid field (FR-056, FR-057) |
| Page | In-page failure region with a retry route; filters/query preserved |
| Site | Custom 404 / 500 with full navigation |

## Caching and headers

| Response | Policy |
| --- | --- |
| Hashed static assets | `Cache-Control: public, max-age=31536000, immutable` |
| HTML | `Cache-Control: no-cache` — session-dependent counts must never be served stale |
| Mutation responses | `Cache-Control: no-store` |

Security headers: `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`,
`X-Frame-Options: DENY`, and a CSP without `unsafe-inline` for scripts. `Secure` cookies, HSTS, and
SSL redirect are enabled in production settings only.

**CSP note.** Because no inline scripts are used (R-007), a strict script CSP is achievable without
nonces. This also satisfies PB-13 — a CSP that names no third-party origin makes an accidental CDN
dependency fail loudly rather than silently working.

## Output escaping

Django autoescaping stays on everywhere. `|safe`, `mark_safe`, and `{% autoescape off %}` are
**prohibited for any visitor-supplied or catalogue-derived value**; permitted only for build-time
constant markup such as the icon sprite, and every use requires an inline justification comment.
Echoed search queries are escaped, never rendered as markup (FR-087).

An automated check fails the build on any `|safe`/`autoescape off` occurrence lacking a
justification comment.
