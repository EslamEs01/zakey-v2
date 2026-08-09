# Security Threat Model

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-004, FR-039, FR-054 – FR-058, FR-074, FR-077, FR-078, FR-095, FR-111 – FR-115.

Scope: a public Egyptian storefront with customer accounts, a staff console, and money. Assets worth protecting: customer personal data, order and payment records, stock truth, staff credentials, and price integrity.

---

## 1. Threats and controls

### T-01 · Broken object-level authorization (IDOR) — **critical**

*A customer requests `/account/orders/1042/` belonging to somebody else.*

- Every customer-facing queryset filters by `request.user` **before** `get_object`; never `Model.objects.get(pk=...)` then check.
- A miss returns **404, not 403** — 403 confirms the record exists (FR-056, INV-010).
- Order lookups by number are still scoped by owner.
- Guest order access requires a signed, expiring token, not a guessable number.
- **Test**: `tests/integration/test_ownership.py` walks every customer-owned model and asserts cross-user access is 404.

### T-02 · Privilege escalation — **critical**

- `is_staff` / `is_superuser` are never in any storefront form, serializer or view; only Super Administrator sets them (FR-057).
- Registration and profile forms use explicit allow-lists of fields, never `fields = "__all__"`.
- Permissions checked server-side in querysets, `has_*_permission` and action handlers (FR-111).
- Group membership changes are audited (FR-113).
- **Test**: attempt to set `is_staff` via every customer-writable form; assert refusal.

### T-03 · Price and total tampering — **critical**

*Browser posts `price=1` or `total=0`.*

- The server **never reads** price, VAT, discount, shipping or total from the request (FR-034). Requests carry variant ids, quantities, coupon code, shipping choice — nothing monetary.
- Totals recomputed from locked database rows inside the order transaction.
- **Test**: post tampered money fields; assert the order is charged the true amount.

### T-04 · Overselling and race conditions — **critical**

Covered in `inventory-integrity.md` §4: row locks, deterministic lock ordering, database check constraints, unique idempotency key. PostgreSQL concurrency tests are mandatory evidence.

### T-05 · CSRF — **high**

- `CsrfViewMiddleware` enabled (FR-003); it is absent today.
- `{% csrf_token %}` added to every mutating form — **zero templates have one today** (`current-state-inventory.md` §3).
- `CSRF_COOKIE_SECURE`, `CSRF_COOKIE_HTTPONLY`, `SameSite=Lax`, and `CSRF_TRUSTED_ORIGINS` set in production.
- Every state change is POST; no GET mutates. Note the account and contact forms are `method="get"` today (`current-state-inventory.md` §4) — converting them to POST is required, not optional.

### T-06 · XSS — **high**

- Django autoescaping on; `|safe` and `mark_safe` are forbidden on any user-supplied value (reviews, contact messages, names).
- Admin-authored rich text is sanitised through an allow-list on save.
- `json_script` is used for the fixture/context payload, never raw interpolation into a `<script>`.
- CSP header: `default-src 'self'`, no `unsafe-inline` for scripts.
- **Test**: submit `<script>` payloads through review, contact and address forms; assert escaped output.

### T-07 · SQL injection — **medium**

ORM everywhere; `raw()` / `extra()` forbidden. Any unavoidable raw SQL uses parameter binding and is reviewed by Claude. Search uses ORM `icontains`, never string-built SQL.

### T-08 · Malicious file upload — **high**

*Product image is a decompression bomb, a polyglot, or an SVG carrying script.*

- Extension allow-list: `.jpg`, `.jpeg`, `.png`, `.webp` for images; `.pdf` for documents.
- Content-type verified by **magic bytes**, not the client-supplied header.
- Pillow verification plus `Image.MAX_IMAGE_PIXELS` guard against decompression bombs; images re-encoded on upload, stripping EXIF and any embedded payload.
- Max size 5 MB images / 10 MB documents.
- **SVG upload is rejected outright** — SVG is an XSS vector and the repository's existing SVGs are build-time assets, not uploads.
- Uploads stored outside the web root, served with `Content-Disposition` and `X-Content-Type-Options: nosniff`; the media directory never executes.
- Randomised stored filenames; original names sanitised for display only.

### T-09 · Authentication attacks — **high**

- Argon2 password hasher; Django validators plus a minimum length of 10.
- Login rate limiting per IP **and** per account with progressive backoff (FR-058).
- Identical response and timing for unknown vs. wrong password — no account enumeration.
- Password reset tokens single-use, time-limited, rate-limited; reset does not reveal whether the email exists (FR-054).
- Session rotation on login and on privilege change; `SESSION_COOKIE_SECURE`, `HttpOnly`, `SameSite=Lax`; idle and absolute timeouts, shorter for staff.
- Staff admin additionally IP-restricted where deployment allows.

### T-10 · Open redirect — **medium**

`next` parameters validated against an allow-list of internal paths using `url_has_allowed_host_and_scheme`. No user-supplied absolute URL is ever redirected to.

### T-11 · Secrets exposure — **critical**

- `SECRET_KEY` is hardcoded today (`config/settings.py:6`) — this **must** move to the environment (FR-001).
- No secret in code, fixtures, templates, logs, admin or the repository; `.env` git-ignored; a pre-commit secret scan runs.
- `DEBUG=False` in production so no traceback leaks configuration (FR-004).

### T-12 · Payment data — **critical**

- **No card number, CVV or PAN is ever stored, logged or transmitted to this system** (FR-077). The architecture never receives them: manual and COD methods only, with any future gateway using a redirect/hosted-field flow.
- Only a `payload_digest` of provider events is stored — never a raw payload.
- Provider credentials from environment only (FR-078).
- Webhooks verify signature, reject replays by unique `provider_event_id`, and are idempotent (FR-074).

### T-13 · Personal data exposure — **high**

- Collect only what fulfilment needs: name, email, phone, address.
- Logs redact passwords, tokens, full phone numbers and full addresses (FR-007, NFR-012).
- Admin masks phone and email except for roles holding `view_full_contact` (FR-112).
- Retention: contact messages 24 months, newsletter until unsubscribe, carts per TTL, orders per Egyptian statutory accounting retention.
- Deletion requests anonymise the customer while preserving order financial records.

### T-14 · Spam and abuse — **medium**

Rate limits plus honeypot fields on newsletter, contact and review submission (FR-095). Reviews require moderation before publication (FR-091). Coupon attempts rate-limited per session to prevent code brute-forcing.

### T-15 · Denial of service — **medium**

Pagination capped; upload sizes capped; `DATA_UPLOAD_MAX_MEMORY_SIZE` and `DATA_UPLOAD_MAX_NUMBER_FIELDS` set; admin exports bounded and offered as downloads rather than in-request rendering; no unbounded dashboard query (FR-102).

### T-16 · Insider and audit-trail threats — **high**

Audit records are append-only and immutable for **everyone including superusers** (FR-114, INV-013) — enforced by the absence of any update/delete code path, not by a permission flag. Staff login, logout, failed login and permission denial are logged (FR-115).

---

## 2. Production security settings (FR-004)

```python
DEBUG = False
SECRET_KEY = env("DJANGO_SECRET_KEY")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS")
```

`python manage.py check --deploy` must report **zero issues** — asserted by a test, not checked by hand.

---

## 3. Backup and restore

Nightly encrypted PostgreSQL dump with 30-day retention plus media backup; **restore rehearsed at least once** before launch (`rollout-and-rollback.md` §5). An unrehearsed backup is not a backup.

---

## 4. Verification

`tests/security/` covers: ownership/IDOR sweep, privilege-escalation attempts, price tampering, CSRF enforcement on every mutating endpoint, XSS payload escaping, upload rejection (bad magic bytes, oversized, SVG, decompression bomb), login rate limiting, open-redirect rejection, log redaction, and `check --deploy` cleanliness. Every threat above maps to at least one named test in `test-strategy.md` §6.
