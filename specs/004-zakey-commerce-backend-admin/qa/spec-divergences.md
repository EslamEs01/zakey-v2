# Specification-vs-implementation divergences (found by T-1806)

Closing the traceability matrix honestly meant reading all 122 functional
requirements against the code that claims to satisfy them. Four things turned
out not to say quite what the repository does. They are recorded here rather
than papered over with a test that names the requirement and proves something
adjacent — which is the specific failure mode `traceability.md` exists to
prevent.

| # | subject | state |
|---|---|---|
| 1 | FR-086 — coupon rejection message | **resolved in code** |
| 2 | FR-132 — localStorage migration adapter | **resolved by supersession** |
| 3 | FR-025 — release on payment failure | ✅ **RESOLVED in code** |
| 4 | `base.html` no-JS notice | ✅ **RESOLVED in the template** |
| 5 | FR-075 — refund cap as a *database* constraint | ✅ **RESOLVED by a constraint trigger** |

**All five are now closed.** Items 3–5 were resolved against the *literal*
specification rather than being treated as discretionary: in each case the
requirement, the design documents, or both already said what had to happen, and
the only thing missing was the implementation.

| # | mechanism | direct tests |
|---|---|---|
| 3 | `orders.services.release_reservations_after_payment_failure`, called from `payments.services.mark_failed` | `apps/orders/tests/test_payment_failure_release.py` (14) · `tests/concurrency/test_refund_cap_and_release_races.py` (2) |
| 4 | `templates/base.html` bilingual `<noscript>` notice | `tests/integration/test_noscript_notice.py` (12) |
| 5 | `payments/migrations/0002_refund_cap_constraint_trigger.py` | `tests/security/test_refund_cap_database.py` (14) · `tests/concurrency/test_refund_cap_and_release_races.py` (2) |

---

## 1. FR-086 — resolved in code

> An exhausted or expired coupon MUST fail closed with **the existing Arabic
> rejection message**.

`apps/promotions/services.py` failed closed, but with *two different* messages
for exactly the two cases the requirement names:

```python
raise CouponError("انتهت صلاحية هذا الكود.")   # expired
raise CouponError("تم استنفاد هذا الكود.")      # exhausted
```

Neither is "the existing rejection message" (`REJECTED_MESSAGE`), so the
requirement was not met. Both now raise `REJECTED_MESSAGE`, in `validate_coupon`
and in `redeem`'s locked re-check.

There is a security argument for the same change: a distinct "this code has
expired" confirms to whoever typed it that the code is *real*, which is the
enumeration oracle the coupon rate limiter (T-1707) exists to close.

**Nothing else referenced the two removed strings** — verified by repository
search — so no test, template or fixture depended on them.

> **Reversible if the business disagrees.** Specific messages are friendlier;
> the requirement, as written, is what forced the generic one. If the business
> wants "this code has expired" back, change the two `raise` statements and
> amend FR-086 — do not leave the code and the requirement disagreeing.

## 2. FR-132 — resolved by supersession

> localStorage cart and wishlist behaviour MUST be replaced through an isolated
> adapter, **keeping `zakey:prototype:v1` handling as a one-time migration path**.

This is a *transition* requirement and the transition is finished. The adapter
was the swap mechanism during Phase 16 — T-1604 lists "`localStorage` migration
adapter" among its deliverables and maps to FR-132. It is now gone:

- `static/src/js/state/storage-adapter.js` no longer exists;
- neither `static/src/js` nor the built `static/dist/js` mentions the key;
- the only surviving copy is a stale artifact in the git-ignored `_site/` export
  — which is also the evidence that it *did* ship before being retired.

**A small process gap, recorded rather than tidied away:** no task line records
the removal. `rollout-and-rollback.md` §3 retires the feature flag and
`fixture_provider.py` together in T-1608, and T-1608's own line names only
`fixture_provider.py`. The adapter went with them, correctly, but silently. The
end state is right; the paper trail for it is one line short.

**The one-time migration path therefore does not exist**, and should not: the
prototype was a reference build (`003-zakey-frontend-reference-build`) that was
never deployed to a customer, so no browser holds `zakey:prototype:v1` to
migrate. Keeping the path would be dead code guarding data that cannot exist.

`tests/integration/test_client_state_removal.py` proves the **end state the
requirement exists to produce** — no web-storage access in any shipped script,
the prototype key absent from source, bundle and templates, the adapter module
really deleted, no basket or money serialised into `#zakey-fixture`, and the
cart rendered server-side. It does not claim a migration path.

## 3. FR-025 — RESOLVED: the hold is released when the order's payment terminally fails

> Reservations MUST be released on **cancellation, payment failure or expiry**,
> and converted to a deduction on fulfilment.

Three of the four triggers are implemented and proven. **Payment failure is
not.**

`apps/payments/services.py::mark_failed` transitions the payment, records an
event, writes an audit row and calls `_sync_order`. It never touches
reservations, and nothing else in `apps/payments` does either — a repository
search for `release`, `reservation` and `restock` across that package returns
nothing. A failed payment leaves the hold **ACTIVE** until staff cancel the
order or the TTL sweeper expires it.

| trigger | implemented | proven by |
|---|---|---|
| cancellation | yes | `apps/inventory/tests/test_movement_reasons.py::TestTheLifecycleWritesTheRightMovement::test_cancelling_an_order_releases_its_reservations` |
| expiry | yes | `apps/inventory/tests/test_release_expired_command.py::TestTheSweep::test_an_expired_reservation_is_released` |
| fulfilment → deduction | yes | `…::test_fulfilment_converts_the_reservation_into_a_deduction` |
| **payment failure** | **no** | **nothing — deliberately not faked** |

### It was never a discretionary decision

`inventory-integrity.md` §3 draws the edge explicitly:

```
        ┌────────┐  fulfil   ┌──────────┐
        │ active │──────────►│ consumed │
        └───┬────┘           └──────────┘
            │ cancel / payment fail
            ▼
        ┌──────────┐
        │ released │
        └──────────┘
```

So the design documents already required it. What made it *look* like a policy
question is a real subtlety, and the implementation turns on getting that right
rather than on choosing a preference.

### Terminal for the order, not for one attempt

`payment-state-machine.md` §2 makes `failed` terminal **per attempt** — a retry
is a new `Payment` row, never a revived one. An order can therefore hold a failed
attempt and a live one at the same time. Releasing on the first failure would
take a customer's basket away while they are still paying.

`release_reservations_after_payment_failure` (in `orders/services.py`) therefore
releases only when **no** attempt on the order remains `pending`, `authorised`,
`captured`, `partially_refunded` or `refunded`. That is the distinction between a
retryable failure and a terminal one, read off the payment model rather than
invented.

| situation | behaviour | test |
|---|---|---|
| only attempt fails | released | `test_the_reservation_is_released_and_the_stock_comes_back` |
| one fails, a retry is pending | **kept** | `test_a_failure_alongside_a_pending_retry_releases_nothing` |
| the retry then fails too | released, once | `test_the_hold_ends_only_when_the_last_attempt_fails` |
| part-captured, remainder declined | **kept** | `test_a_captured_payment_keeps_the_hold_even_if_a_later_attempt_fails` |
| the same callback delivered 3× | released once | `test_a_duplicate_failure_callback_releases_nothing_the_second_time` |
| two failures land simultaneously | released once | `test_two_simultaneous_failures_release_the_hold_once` |
| the same callback ×4 concurrently | released once | `test_the_same_failure_callback_delivered_four_times_at_once_releases_once` |
| another order holds stock | untouched | `test_it_cannot_release_another_order_s_reservation` |

### Integrity properties

* **Atomic** — one transaction, locking `Order` then `StockItem`, the same order
  `transition()` uses, so the two cannot deadlock against each other.
* **Idempotent** — `inventory.services.release` is a no-op on any reservation
  that is not `active`; `mark_failed` also stops appending a duplicate
  `failed` event on replay.
* **Concurrency-safe** — `select_for_update` on the order serialises two
  simultaneous failure callbacks.
* **Scoped** — reservations are read through `locked.reservations`, so another
  order's hold is unreachable by construction.
* **Append-only** — every release goes through the inventory service, writing a
  `StockMovement(release)` with before/after snapshots. `verify_stock_integrity`
  reports no drift afterwards, which is asserted. No history is rewritten and no
  balance is edited directly.

All four FR-025 triggers — cancellation, **payment failure**, expiry, and
conversion to a deduction on fulfilment — are now implemented and proven.

## 4. `templates/base.html` — customer-facing copy is now understating the product

`templates/base.html:16` tells a visitor without JavaScript:

> يمكنك تصفح الصفحات والمنتجات، ولتشغيل السلة والفلاتر والمفضلة يرجى تفعيل JavaScript.
> *("You can browse pages and products; to run the cart, filters and wishlist,
> please enable JavaScript.")*

That was true of the prototype. It is **no longer true**: the strengthened no-JS
suite (`tests/e2e/no-js.spec.js`, FR-136) now drives a customer through adding a
product, seeing a server-rendered total, changing quantity, removing the line,
sorting the catalogue and reaching checkout — all with `javaScriptEnabled:
false`. The note tells customers a working feature is unavailable.

### Resolved: a bilingual notice that says the true thing

`templates/base.html` now carries:

> <span lang="ar">جافاسكريبت مطلوب للعناصر التفاعلية في المتجر، مثل القوائم المنسدلة والنوافذ الحوارية. التصفح والشراء وإتمام الطلب تعمل بدونه.</span>
> <span lang="en">JavaScript is required for interactive storefront features such as dropdown menus and dialogs. Browsing, shopping and checkout work without it.</span>

* **Bilingual with per-language markup.** Each sentence is its own `<span>` with
  `lang` and `dir`. Without `dir="ltr"` the English run is reordered by the RTL
  page and its punctuation lands at the wrong end; without `lang` a screen reader
  pronounces English with Arabic phonemes (NFR-010).
* **The page direction is untouched** — `<html lang="ar-EG" dir="rtl">` is
  asserted unchanged.
* **The established design is untouched** — same `.noscript-note` class, same
  CSS. A copy fix was not used as an excuse to restyle anything.
* **Invisible in captures.** `<noscript>` content is not rendered when scripting
  is on, and a test asserts neither "JavaScript" nor "جافاسكريبت" appears
  anywhere *outside* the element — so a stray copy cannot leak into a snapshot.
  **No visual snapshot was updated in this session.**
* **No draft wording** — a test scans for `TODO`, `FIXME`, `XXX`, `Lorem`,
  `placeholder` and Arabic filler.

The specific falsehood is pinned so it cannot return: a test asserts the string
"لتشغيل السلة والفلاتر والمفضلة يرجى تفعيل" is **absent**.

## 5. FR-075 — RESOLVED: the refund cap is now a database constraint

> Refunds MUST NOT exceed captured minus already-refunded, enforced by a
> **database constraint plus** a locked service check.

The locked service check exists and is genuinely proven, including under real
thread contention: ten threads each refunding 200 against a 1000 capture produce
exactly five successes totalling 1000, which only holds because the remaining
balance is read inside `select_for_update`.

**The database constraint does not exist.** The entire payments schema carries
two constraints, both plain positivity checks (`apps/payments/models.py`):

```python
CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive")
CheckConstraint(condition=Q(amount__gt=0), name="refund_amount_positive")
```

There is no trigger, no denormalised `refunded_total`, and a cross-row sum cap
is not expressible as a Django `CheckConstraint` — it needs either a
denormalised column plus a constraint, or a trigger.

**Why this matters more than a wording quibble.** The repository's stated
philosophy, in `handoff.md` §2, is that load-bearing invariants are "enforced by
a database constraint rather than by convention alone" — and `reserved <=
on_hand` really is. Refunds are the money-losing invariant, and there the
service layer is the only thing standing between the shop and paying a customer
twice. Any second code path that writes a `Refund` row — an import, a shell
session, a future admin action, a repaired migration — bypasses the check.

### Resolved: a constraint trigger, and the lock inside it

`payments/migrations/0002_refund_cap_constraint_trigger.py` installs a
`CONSTRAINT TRIGGER` on `payments_refund`, firing `AFTER INSERT OR UPDATE`,
`DEFERRABLE INITIALLY IMMEDIATE`.

**The lock is the load-bearing part, not the sum.** Under `READ COMMITTED` two
concurrent transactions cannot see each other's uncommitted refunds, so both
would compute the same stale total and both would pass. The trigger therefore
takes `SELECT ... FOR UPDATE` on the parent payment *before* summing:

```sql
SELECT CASE WHEN p.state IN ('captured','partially_refunded','refunded')
            THEN p.amount ELSE 0 END
  INTO captured
  FROM payments_payment p
 WHERE p.id = NEW.payment_id
   FOR UPDATE;
```

The second transaction blocks until the first commits, re-reads, and sees the
money already returned. The database — not the service — is what cannot be raced.

Encoding the state in the cap also gives the second half of FR-075's wording for
free: "captured minus already-refunded" means a payment that never captured has
nothing refundable, so a completed refund against a `pending` payment is refused
by the database.

### What is proven, and how it is bypassed on purpose

Every test writes **around** `payments.services.refund`. A test that went through
the service would only prove the service works, which was never in doubt.

| bypass | result | test |
|---|---|---|
| direct `Refund.objects.create` | `IntegrityError` | `test_a_direct_orm_create_over_the_cap_is_refused` |
| `bulk_create` (skips `save()`) | `IntegrityError` | `test_bulk_create_over_the_cap_is_refused` |
| raw SQL `INSERT`, no Django in the path | `IntegrityError` | `test_raw_sql_over_the_cap_is_refused` |
| `UPDATE` lifting an existing refund | `IntegrityError` | `test_an_update_that_lifts_a_refund_over_the_cap_is_refused` |
| parking a `pending` refund, completing it later | `IntegrityError` | `test_flipping_a_pending_refund_to_completed_over_the_cap_is_refused` |
| refund against an uncaptured payment | `IntegrityError` | `test_a_refund_against_an_uncaptured_payment_is_refused` |
| ten concurrent direct writes, 200 each, 1000 captured | exactly 5 accepted, 5 refused, total 1000.00 | `test_concurrent_direct_writes_cannot_together_exceed_the_capture` |

Valid behaviour is pinned too: partial refunds below the cap, refunding *exactly*
the captured amount to the piastre, pending and failed refunds not consuming the
cap, and two payments holding independent caps. The service still raises its
readable `OverRefund` first — the trigger is the authority behind it, not a
replacement for the friendly error.

The migration is proven to run on a clean database by
`test_the_migration_installed_a_constraint_trigger`, which reads `pg_trigger` in
the freshly-migrated test database and asserts the trigger exists **and** is a
constraint trigger.

**SQLite is not a consideration here and was not allowed to become one.**
`conftest.py` refuses to run the suite on anything but PostgreSQL (FR-002,
NFR-005), so there is no environment in which this constraint is silently
skipped — no `connection.vendor` guard, no conditional migration, no test that
passes by not checking.
