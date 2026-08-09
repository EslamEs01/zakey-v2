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
| 3 | FR-025 — release on payment failure | ⚠️ **OPEN — product decision** |
| 4 | `base.html` no-JS notice | ⚠️ **OPEN — belongs to T-1901** |
| 5 | FR-075 — refund cap as a *database* constraint | ⚠️ **OPEN — schema change** |

Items 3–5 are deliberately left open: a product decision about oversell risk,
storefront copy that should not move while seven visual comparisons are
mid-approval, and a schema migration. None is mine to take unilaterally.

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

## 3. FR-025 — ⚠️ OPEN, and a product decision

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

**Why this was not simply "fixed".** Releasing on the first failed attempt would
drop the customer's hold mid-retry: a mistyped card would hand their stock to
someone else while they are still checking out. Whether a failed attempt should
release immediately, release after N attempts, or rely on the TTL sweeper is a
**product decision about customer experience and oversell risk**, not a defect
with an obvious correct answer.

### What the owner of `apps/payments` must decide

1. **`mark_failed` releases the reservation** — matches FR-025 literally; risks
   losing the hold during a legitimate retry.
2. **TTL expiry remains the only path** — matches today's code; amend FR-025 to
   say so explicitly, e.g. *"…on cancellation or expiry; a failed payment
   attempt leaves the reservation to the TTL sweeper."*
3. **Release after a threshold** — a middle path, and new work.

Until that is decided, FR-025's row in `traceability.md` is evidenced by tests
covering three of its four triggers. That is stated here so the ✅ is not read
as "all four are proven".

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

**Deliberately not changed here.** It is storefront copy on every page, and the
seven `account`/`checkout` visual comparisons in `qa/visual-approval-ledger.md`
are still awaiting approval; editing shared chrome mid-approval would muddy that
review for a defect that is cosmetic and outside T-1806's scope. It belongs to
whoever closes T-1901.

Suggested replacement text, for whoever takes it:

> يمكنك التسوق وإتمام طلبك بدون JavaScript؛ تفعيله يضيف تحسينات في التصفح فقط.
> *("You can shop and complete your order without JavaScript; enabling it only
> adds browsing enhancements.")*

## 5. FR-075 — ⚠️ OPEN: the refund cap has no database constraint

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

FR-075 is mapped to the tests that prove the normative core (the bound holds,
and holds under contention) plus a new test asserting `refund_amount_positive`
is enforced by PostgreSQL — which is a real part of the bound, because a
negative refund row written behind the service would *raise* the refundable
amount and let the next refund exceed the capture.

**Open task**: add the missing constraint (`apps/payments/models.py` + a
migration), or amend FR-075 to say the cap is service-enforced under a row lock.
Do not leave the code and the requirement disagreeing on something this
expensive.
