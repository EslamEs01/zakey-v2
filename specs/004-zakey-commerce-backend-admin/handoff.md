# ZAKEY v2 — handoff report (T-2007)

## 1. No production deployment occurred

Confirmed for the whole of this implementation:

- no commit, push, merge, rebase, pull request or tag;
- no remote was added, changed or contacted;
- no VPS or any remote host was accessed;
- no deployment was performed;
- no production database, service or file was touched;
- no external provider (mail, monitoring, DNS, TLS, payments) was configured.

The repository sits on branch `004-zakey-commerce-backend-admin` at HEAD
`98237d7` with the work uncommitted in the working tree, exactly as it was
received. `git diff --check` is clean.

Everything in `deploy/` is a **reviewed and locally validated artifact**, not a
running system. `zakey-nginx.conf` still carries `ZAKEY_HOSTNAME_PLACEHOLDER`
precisely so nobody can mistake it for a configured host.

## 2. What was built

A Django 5.2 / PostgreSQL 16 commerce backend behind the approved Arabic-first,
RTL storefront: 12 domain apps, a Jazzmin staff admin with nine roles, and the
13 public routes preserved against a captured visual baseline.

Load-bearing decisions, each enforced by a database constraint rather than by
convention alone:

- **`reserved <= on_hand`** as a `CheckConstraint` — overselling is structurally
  impossible even if every service above it is wrong.
- **VAT extracted from gross**, never added; catalogue prices are VAT-inclusive.
- **Insert-then-select idempotency** on `Order.idempotency_key`; ten replays
  produce one order.
- **Deterministic lock ordering by `variant_id`** — two carts holding {A,B} and
  {B,A} cannot deadlock.
- **Append-only ledgers** (`StockMovement`, `PaymentEvent`, `OrderEvent`,
  `AuditLog`) with no update or delete path for anyone, superusers included.
- **Archive, never delete**: `OrderLine.variant` is `PROTECT`, so a product a
  customer actually bought cannot be removed from the catalogue.

## 3. Defects found and fixed during implementation

These were found by tests written for this work, not reported by anyone:

| defect | consequence had it shipped |
|---|---|
| `OrderLine.variant` was `SET_NULL` | deleting an ordered product silently succeeded and blanked history |
| `django-import-export` default-insecure | any staff member could import or export any model, past the role matrix |
| Dashboard showed all widgets to all staff | a content editor could read payment failures and customer names |
| Log redaction left bearer tokens in clear | `Authorization: Bearer <token>` redacted only the word "Bearer" |
| `cvv=123` was not redacted | a three-digit CVV slipped past the card-length rule |
| Pillow 11.3.0 (25 advisories) | untrusted uploads parsed by a vulnerable decoder |
| `pip-audit` scanned the wrong environment | a false "no vulnerabilities" clean bill |
| Contact page dropped 2 database FAQs | a fixture-era template filter silently emptied the accordion |
| QA gate depended on a fresh database | reservations accumulated until checkout correctly refused |
| `release_expired_reservations` did not exist | the scheduled cron job in the runbook would have failed on day one |
| Missing `test_deploy_check.py`, `test_no_card_data.py` | two security tasks were checked with no test behind them |

## 4. Verified state at handoff

| gate | result |
|---|---|
| Django suite (isolated, with coverage) | 1363 passed, 0 failed, 0 errors, **0 skipped** |
| Coverage | 88.06% overall; **91.27%** on services/models/permissions (floor 85%) |
| PostgreSQL concurrency suite | 21 passed — all 10 scenarios in `test-strategy.md` §4 |
| Playwright E2E + accessibility | 400 passed |
| No-JS matrix (4 viewports) | 40 passed |
| Dependency audit (`pip-audit` on the lockfile) | 0 vulnerabilities across 25 packages |
| `manage.py check` / `makemigrations --check` | no issues / no changes detected |
| `npm run qa` | deterministic: 489 passed / 7 failed on two consecutive runs |

## 5. What is NOT done

**T-1901 — seven visual comparisons** (`account` ×4, `checkout` ×3) have not been
approved. Approval requires opening the expected, actual and diff PNGs, and the
tooling available during implementation could not display images. Pixel counts
and band analysis are not visual review, so no snapshot was updated. The
close-out procedure is in `qa/visual-approval-ledger.md`.

**T-1906 — `npm run qa` is not green.** It is deterministic, but a deterministic
red is still red. It exits 0 only once the seven comparisons above are resolved.

**T-2006 — awaiting the business.** See §6.

### Closed since this report was first written

**T-1806 — traceability is complete.** 122 requirements · 122 claimed by a task ·
**121 with test evidence · 0 problems**; the 122nd is FR-135, which is `📄` by
design. 68 gaps were closed with real assertions, ~540 tests added, and every
mapping reviewed individually. The generator was also tightened so a module-level
claim no longer credits every test in a file to every requirement its header
lists. Record: `qa/traceability-closure.md`.

**T-2003 — rollback rehearsed.** Release B → release A against real git releases,
a real health endpoint and a real PostgreSQL scratch restore, with the service
manager mocked; 32 tests, every failure path exercised. It found a real defect —
`rollback()` never entered `ZAKEY_ROOT`, so `uv sync` and `collectstatic` ran in
the operator's shell directory. Fixed. Record: `qa/rollback-rehearsal.md`.

### Three things T-1806 found, since resolved

Full detail and evidence in **`qa/spec-divergences.md`**. Each was resolved
against the literal specification rather than closed with a test that names the
requirement and proves something adjacent.

- **FR-025 — a failed payment now releases the hold.** `inventory-integrity.md`
  §3 always drew the edge (`active ──cancel / payment fail──► released`); it was
  simply never wired up, so a declined card kept stock off the shelf until staff
  noticed or the TTL swept it. The subtlety is that `failed` is terminal *per
  attempt*, so the release waits until no attempt on the order is still pending,
  authorised or captured — a retry keeps its basket. Atomic, idempotent under
  duplicate callbacks, serialised by a lock on the order, scoped so it cannot
  touch another order's stock, and recorded as a `StockMovement(release)`.
- **FR-075 — the refund cap is now enforced by the database.** A
  `CONSTRAINT TRIGGER` (`payments/migrations/0002`) takes
  `SELECT ... FOR UPDATE` on the parent payment before summing completed
  refunds, so two concurrent writers cannot both pass a stale total. Proven
  against direct ORM writes, `bulk_create`, raw SQL, `UPDATE`, a parked pending
  refund completed later, and ten concurrent threads. The money-losing invariant
  now lives in the schema alongside `reserved <= on_hand`, as §2 always claimed.
- **`templates/base.html` — the no-JS notice tells the truth.** It said the cart,
  filters and wishlist needed JavaScript; the no-JS suite proves they do not. It
  is now bilingual, with per-language `lang`/`dir`, and says scripting is needed
  for the interactive layer only. `<noscript>` content never renders in a
  scripted browser, and a test asserts the text appears nowhere outside the
  element — **no visual snapshot was updated.**

## 6. The one external dependency

ZAKEY cannot invent shipping rates or an installation fee. Still required from
the business:

1. **Shipping rates per zone**, for each active shipping method.
2. **The installation fee**, and the governorates where installation is offered.

Every technical safeguard around them is built and tested: development values
are flagged `is_placeholder=True`; production refuses to quote a placeholder
(`ZAKEY_ALLOW_PLACEHOLDER_RATES` defaults to `False`); `has_unapproved_rates()`
is the launch gate; and approved values are entered in the admin with no code
change. A free-over-threshold quote is exempt because zero misleads nobody.

## 7. First deployment — what the operator must do

1. Provision PostgreSQL 16 and create the `zakey` database and role.
2. Write `/etc/zakey/zakey.env` (root:zakey, 0640) from `.env.example`, with a
   real 50+ character `DJANGO_SECRET_KEY`. `zakey-deploy.sh validate` refuses
   the example values — verified by test.
3. Install `deploy/zakey-web.service` and `deploy/zakey-nginx.conf`, replacing
   `ZAKEY_HOSTNAME_PLACEHOLDER` with the approved hostname. Issue TLS.
4. Run `deploy/zakey-deploy.sh deploy`.
5. `createsuperuser`, then assign every staff member exactly one of the nine
   roles.
6. Enter the approved shipping and installation rates; confirm
   `has_unapproved_rates()` is `False`.
7. Run `deploy/zakey-backup.sh`, then `deploy/zakey-restore-drill.sh` against
   that dump. A backup that has never been restored is a hypothesis.
8. Install the cron schedule in `operations.md` §1.
9. Resolve the seven visual comparisons before treating the storefront as
   signed off.
