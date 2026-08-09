# ZAKEY operations — monitoring, roles and staff workflows (T-2004, T-2005)

**Nothing in this document has been deployed.** No VPS was accessed, no DNS or
TLS was issued, no monitoring provider, mail provider or alert channel has been
configured. What follows is the reviewed, locally validated procedure to be
carried out by whoever performs the first deployment.

---

## 1. Health and monitoring (T-2004)

### Probes

| check | command | healthy result |
|---|---|---|
| Application up | `curl -fsS http://127.0.0.1:8001/healthz/` | `200`, `{"status":"ok"}` |
| Database reachable | `manage.py check --database default` | no issues |
| Migrations applied | `manage.py migrate --check` | exit 0 |
| Stock ledger consistent | `manage.py verify_stock_integrity` | exit 0, "No stock drift found" |
| Payments reconciled | `manage.py reconcile_payments` | exit 0, "No divergence found" |

`/healthz/` reports database connectivity and **nothing about configuration**
(FR-006), and Nginx restricts it to loopback so it is not an internet-facing
information source.

### Schedule

```cron
*/15 * * * *  cd /srv/zakey && .venv/bin/python manage.py release_expired_reservations
0    * * * *  cd /srv/zakey && .venv/bin/python manage.py reconcile_payments
30   3 * * *  cd /srv/zakey && .venv/bin/python manage.py verify_stock_integrity
0    2 * * *  /srv/zakey/deploy/zakey-backup.sh
0    4 * * 0  cd /srv/zakey && .venv/bin/python manage.py purge_expired_data --apply
```

`release_expired_reservations` is the load-bearing one. Reservations that never
expire remove stock from sale permanently — the shop sells out without selling
anything. Everything else is detection; that one is prevention.

`purge_expired_data` is the only scheduled destructive job. It never touches
orders, payments, refunds or the audit log.

### Alert conditions

Alert when any of these is true. Each is a real symptom, not a threshold picked
for the sake of having one.

| condition | why it matters |
|---|---|
| `verify_stock_integrity` exits non-zero | stock changed without a ledger entry — overselling becomes possible |
| `reconcile_payments` exits non-zero | the ledger and an order's payment status disagree; money is unaccounted for |
| `/healthz/` non-200 for 2 consecutive checks | the site is down or the database is unreachable |
| `zakey-backup.sh` non-zero, or no new dump in 26h | the backup is silently not happening |
| Sustained 5xx rate above baseline | a regression is in production |
| `AuditAction.LOGIN_FAILED` spike for staff accounts | credential stuffing against the admin |
| Disk above 85% on the backup volume | the next backup will fail |

No alerting provider is configured. Wiring these to a channel is a deployment
step, not something this repository can claim.

### Error reporting

Structured logging is configured with a redaction filter on every handler
(`apps/core/logging.py`). It scrubs passwords, tokens, bearer tokens, whole
`Authorization` headers, CVV/PAN-shaped values, emails and Egyptian mobile
numbers before a record reaches any sink, so shipping logs to an aggregator does
not ship personal data with them.

---

## 2. The nine roles (T-2005)

Created and reconciled idempotently by `manage.py setup_roles`. Assign each
staff member **exactly one**. Server-side enforcement is the boundary; the menu
only reflects it (FR-111).

| role | may change | may read | never |
|---|---|---|---|
| Super Administrator | everything except append-only ledgers | everything | edit an audit row, stock movement, payment or order event |
| Store Manager | catalogue, stock levels, orders, payments, coupons, content, site settings | audit log | delete anything an order references |
| Catalogue Manager | products, variants, images, specs, categories, collections, brands, coupons, reviews | stock levels | orders, payments, customers |
| Inventory Manager | stock adjustments, movements | products, variants, orders | prices, orders, payments |
| Order Fulfilment | order status, notes, addresses | stock, products, customers, shipping | prices, payments, refunds, coupons |
| Customer Service | orders, customer profiles, addresses, reviews, contact messages | payments, coupons | refunds, prices, catalogue |
| Finance | payments, refunds, payment methods, order status | orders, coupons, stock, audit log | catalogue, customers' addresses |
| Content Manager | home sections, banners, partners, FAQs, pages, navigation, newsletter, reviews | catalogue | orders, payments, customers |
| Read-only Auditor | **nothing** | everything | any write, anywhere |

A staff account with **no** role can sign into the admin and see nothing. That
is the correct default: access is granted deliberately, never inherited.

### Core workflows

**Adjust stock.** Inventory → أرصدة المخزون → select → *adjust stock*. Levels are
never typed in directly: the action demands a delta and a reason and writes a
ledger row, so every movement is attributable (FR-021, FR-105).

**Fulfil an order.** Orders → select → *بدء التجهيز*. This consumes the
reservation and marks the order fulfilled. Status moves only along the approved
edges; an illegal transition is refused with the reason.

**Refund.** Payments → Refunds → add. The sum of refunds can never exceed the
captured amount (INV-004), enforced under a row lock.

**Retire a product.** Catalogue → Products → select → *أرشفة المحدد*. Never
delete: a product an order references cannot be deleted, and archiving keeps
order history resolving (FR-014, FR-109). Restoring returns it as a **draft**,
never straight back to published.

**Moderate a review.** Reviews → select → approve or reject. "Verified purchase"
is derived from order history and cannot be set by hand (FR-092).

**Bulk catalogue edit.** Products / Variants / Stock thresholds / Coupons support
import with a dry-run preview. Orders and payments are **export-only**. Every
import writes an audit row naming the staff member.

**Associate a guest order.** Orders → select → *ربط الطلب بحساب صاحب البريد*.
Deliberately manual: registering with an address must never hand over an order
history (FR-059).

---

## 3. First-run bootstrap

```bash
cd /srv/zakey
uv run python manage.py migrate --noinput
uv run python manage.py setup_roles
uv run python manage.py createsuperuser      # interactive; never in automation
```

Then assign each staff member one role in the admin.

**`seed_demo` is never run in production.** It refuses when real orders exist,
and the deploy script does not invoke it at all (asserted by
`tests/security/test_deployment_artifacts.py`).
