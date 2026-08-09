"""Inventory services (FR-023 – FR-029, INV-001).

Every mutation here runs inside a transaction and takes ``SELECT ... FOR UPDATE``
on the affected ``StockItem`` rows.

**Lock ordering is the whole trick.** Rows are always locked in ascending
``variant_id`` order. Two carts holding variants {A, B} and {B, A} would deadlock
without it; sorting means both take A then B.
"""

from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from apps.audit.middleware import get_request_id

from .models import (
    MovementReason,
    ReservationState,
    StockItem,
    StockLedgerReconciliation,
    StockMovement,
    StockReservation,
)


class InsufficientStock(ValidationError):
    """Raised when a requested quantity exceeds what is available."""

    def __init__(self, variant, requested: int, available: int):
        self.variant = variant
        self.requested = requested
        self.available = available
        super().__init__(
            f"الكمية المطلوبة غير متاحة لـ {getattr(variant, 'sku', variant)}: "
            f"طُلب {requested} والمتاح {available}."
        )


def lock_stock_items(variant_ids) -> dict[int, StockItem]:
    """Lock stock rows in deterministic order to prevent deadlock."""
    ordered = sorted(set(int(v) for v in variant_ids))
    items = (
        StockItem.objects.select_for_update()
        .filter(variant_id__in=ordered)
        .order_by("variant_id")
    )
    return {item.variant_id: item for item in items}


def _record(
    item: StockItem,
    delta: int,
    reason: str,
    *,
    on_hand_before: int,
    reserved_before: int,
    order=None,
    actor=None,
    note: str = "",
) -> StockMovement:
    return StockMovement.objects.create(
        stock_item=item,
        delta=delta,
        reason=reason,
        on_hand_before=on_hand_before,
        on_hand_after=item.on_hand,
        reserved_before=reserved_before,
        reserved_after=item.reserved,
        order=order,
        actor=actor,
        note=note,
        request_id=get_request_id() or "",
    )


@transaction.atomic
def reserve(variant, quantity: int, *, order=None, actor=None, ttl_minutes: int | None = None):
    """Reserve stock for one variant. Caller supplies the transaction for multi-line use."""
    if quantity <= 0:
        raise ValidationError("الكمية يجب أن تكون أكبر من صفر.")

    item = (
        StockItem.objects.select_for_update()
        .select_related("variant")
        .get(variant=variant)
    )
    if item.available < quantity:
        raise InsufficientStock(item.variant, quantity, item.available)

    on_hand_before, reserved_before = item.on_hand, item.reserved
    item.reserved += quantity
    item.save(update_fields=["reserved", "updated_at"])

    if ttl_minutes is None:
        from apps.core.models import SiteSetting

        ttl_minutes = SiteSetting.objects.get_solo().reservation_ttl_minutes

    reservation = StockReservation.objects.create(
        stock_item=item,
        order=order,
        quantity=quantity,
        state=ReservationState.ACTIVE,
        expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
    )
    _record(
        item,
        quantity,
        MovementReason.RESERVE,
        on_hand_before=on_hand_before,
        reserved_before=reserved_before,
        order=order,
        actor=actor,
    )
    return reservation


@transaction.atomic
def release(reservation: StockReservation, *, actor=None, expired: bool = False):
    """Release an active reservation. Releasing twice is a safe no-op."""
    reservation = StockReservation.objects.select_for_update().get(pk=reservation.pk)
    if reservation.state != ReservationState.ACTIVE:
        return reservation

    item = StockItem.objects.select_for_update().get(pk=reservation.stock_item_id)
    on_hand_before, reserved_before = item.on_hand, item.reserved
    item.reserved = max(0, item.reserved - reservation.quantity)
    item.save(update_fields=["reserved", "updated_at"])

    reservation.state = ReservationState.EXPIRED if expired else ReservationState.RELEASED
    reservation.save(update_fields=["state", "updated_at"])

    _record(
        item,
        -reservation.quantity,
        MovementReason.RELEASE,
        on_hand_before=on_hand_before,
        reserved_before=reserved_before,
        order=reservation.order,
        actor=actor,
        note="انتهاء صلاحية الحجز" if expired else "إلغاء الحجز",
    )
    return reservation


@transaction.atomic
def fulfill(reservation: StockReservation, *, actor=None):
    """Convert a reservation into a real deduction (FR-025)."""
    reservation = StockReservation.objects.select_for_update().get(pk=reservation.pk)
    if reservation.state != ReservationState.ACTIVE:
        raise ValidationError("لا يمكن تنفيذ حجز غير نشط.")

    item = StockItem.objects.select_for_update().get(pk=reservation.stock_item_id)
    on_hand_before, reserved_before = item.on_hand, item.reserved
    item.on_hand -= reservation.quantity
    item.reserved -= reservation.quantity
    item.save(update_fields=["on_hand", "reserved", "updated_at"])

    reservation.state = ReservationState.CONSUMED
    reservation.save(update_fields=["state", "updated_at"])

    _record(
        item,
        -reservation.quantity,
        MovementReason.FULFILL,
        on_hand_before=on_hand_before,
        reserved_before=reserved_before,
        order=reservation.order,
        actor=actor,
    )
    return reservation


@transaction.atomic
def adjust(variant, delta: int, reason: str, *, actor=None, note: str = ""):
    """Staff stock adjustment. A reason is mandatory (FR-021, FR-022)."""
    if delta == 0:
        raise ValidationError("التغيير يجب ألا يساوي صفرًا.")
    if reason not in MovementReason.values:
        raise ValidationError(f"سبب غير معروف: {reason}")

    item = StockItem.objects.select_for_update().select_related("variant").get(variant=variant)
    on_hand_before, reserved_before = item.on_hand, item.reserved
    new_on_hand = item.on_hand + delta
    if new_on_hand < 0:
        raise ValidationError("لا يمكن أن يصبح المخزون بالسالب.")
    if new_on_hand < item.reserved:
        raise ValidationError(
            f"لا يمكن خفض المخزون إلى {new_on_hand} بينما يوجد {item.reserved} محجوز."
        )

    item.on_hand = new_on_hand
    item.save(update_fields=["on_hand", "updated_at"])
    return _record(
        item,
        delta,
        reason,
        on_hand_before=on_hand_before,
        reserved_before=reserved_before,
        actor=actor,
        note=note,
    )


@transaction.atomic
def restock_return(variant, quantity: int, *, actor=None, note: str = ""):
    """Explicit staff decision to put returned goods back (FR-028).

    Never automatic: a refund does not restock by itself.
    """
    if quantity <= 0:
        raise ValidationError("الكمية يجب أن تكون أكبر من صفر.")
    return adjust(variant, quantity, MovementReason.RETURN, actor=actor, note=note)


def verify_stock_integrity(*, sku: str | None = None, now=None) -> list[dict]:
    """Report inventory drift. **Never repairs it** (T-0606, FR-027).

    A stock tool that silently corrects what it finds destroys the evidence of
    the bug that caused the drift, and the next drift then looks like the first.
    So this function only reads.

    Integrity is checked against the before/after snapshots on the ledger, not
    by summing ``delta``: ``delta`` is the magnitude of an operation and its
    meaning varies by reason (a RESERVE moves ``reserved``, not ``on_hand``),
    so a sum of deltas is not a balance.

    Returns one dict per drift. An empty list means the ledger, the reservations
    and the stored balances all agree.
    """
    now = now or timezone.now()
    items = StockItem.objects.select_related("variant__product").order_by("variant_id")
    if sku is not None:
        items = items.filter(variant__sku=sku)

    drifts: list[dict] = []

    def report(item, check: str, stored, derived, note: str = "") -> None:
        drifts.append(
            {
                "sku": item.variant.sku,
                "check": check,
                "stored": stored,
                "derived": derived,
                "note": note,
            }
        )

    item_list = list(items)
    by_id = {item.pk: item for item in item_list}

    # One pass over the ledger for every item in scope, oldest first.
    movements = (
        StockMovement.objects.filter(stock_item__in=item_list)
        .order_by("stock_item_id", "created_at", "id")
        .values(
            "stock_item_id",
            "id",
            "on_hand_before",
            "on_hand_after",
            "reserved_before",
            "reserved_after",
        )
    )
    # Discontinuities a human has explicitly examined and explained. Keyed on
    # the exact gap AND the exact values, so a reconciliation stops applying the
    # moment the underlying data differs from what was reviewed — it can never
    # silently absorb a later, unrelated break.
    reconciled = {
        (r["from_movement_id"], r["to_movement_id"], r["field"],
         r["observed_before"], r["observed_after"])
        for r in StockLedgerReconciliation.objects.filter(
            stock_item__in=item_list
        ).values(
            "from_movement_id", "to_movement_id", "field",
            "observed_before", "observed_after",
        )
    }

    chain: dict[int, dict] = {}
    for movement in movements:
        item = by_id[movement["stock_item_id"]]
        previous = chain.get(item.pk)
        if previous is not None:
            for field in ("on_hand", "reserved"):
                before, after = previous[f"{field}_after"], movement[f"{field}_before"]
                if before == after:
                    continue
                if (previous["id"], movement["id"], field, before, after) in reconciled:
                    continue  # examined, explained, recorded
                report(
                    item,
                    "ledger_chain",
                    before,
                    after,
                    f"{field} breaks between movement {previous['id']} "
                    f"and {movement['id']}",
                )
        chain[item.pk] = movement

    # Active reservations must add up to the reserved column.
    reserved_sums = dict(
        StockReservation.objects.filter(
            stock_item__in=item_list, state=ReservationState.ACTIVE
        )
        .values_list("stock_item_id")
        .annotate(total=models.Sum("quantity"))
        .values_list("stock_item_id", "total")
    )
    stale_counts = dict(
        StockReservation.objects.filter(
            stock_item__in=item_list, state=ReservationState.ACTIVE, expires_at__lt=now
        )
        .values_list("stock_item_id")
        .annotate(total=models.Count("id"))
        .values_list("stock_item_id", "total")
    )

    for item in item_list:
        head = chain.get(item.pk)
        # No movements at all is a legitimate seeded opening balance, not drift.
        if head is not None:
            if head["on_hand_after"] != item.on_hand:
                report(item, "ledger_head", item.on_hand, head["on_hand_after"], "on_hand")
            if head["reserved_after"] != item.reserved:
                report(item, "ledger_head", item.reserved, head["reserved_after"], "reserved")

        active_total = reserved_sums.get(item.pk, 0)
        if active_total != item.reserved:
            report(
                item,
                "reserved_sum",
                item.reserved,
                active_total,
                "reserved column disagrees with the sum of active reservations",
            )

        if item.on_hand < 0:
            report(item, "invariant", item.on_hand, 0, "on_hand is negative")
        if item.reserved < 0:
            report(item, "invariant", item.reserved, 0, "reserved is negative")
        if item.reserved > item.on_hand:
            # INV-001. A CheckConstraint forbids this, so seeing it means the
            # constraint itself was dropped or bypassed.
            report(item, "invariant", item.reserved, item.on_hand, "reserved exceeds on_hand")

        stale = stale_counts.get(item.pk, 0)
        if stale:
            report(item, "stale_reservation", stale, 0, "active reservations past expiry")

    return drifts


@transaction.atomic
def reconcile_ledger_break(
    *, stock_item, field: str, from_movement, to_movement, reason: str, actor=None
) -> "StockLedgerReconciliation":
    """Record an audited explanation for one ledger discontinuity (FR-021).

    This does **not** touch the movement ledger: the discontinuity stays exactly
    as it happened, because an append-only record that can be tidied up is not
    an audit trail. What it adds is a separate, equally append-only row saying
    who examined this specific gap and why it is accounted for.

    Idempotent: a unique constraint on (from_movement, to_movement, field) makes
    a second call return the existing record rather than stacking explanations.

    Refuses if the values it was asked to reconcile are not the values actually
    in the ledger — otherwise a stale or copy-pasted repair could silently cover
    a different, real break.
    """
    from .models import StockLedgerReconciliation

    if field not in {"on_hand", "reserved"}:
        raise ValidationError("الحقل يجب أن يكون on_hand أو reserved.")
    if not (reason or "").strip():
        raise ValidationError("سبب التسوية مطلوب.")

    observed_before = getattr(from_movement, f"{field}_after")
    observed_after = getattr(to_movement, f"{field}_before")
    if observed_before == observed_after:
        raise ValidationError("لا يوجد انقطاع بين هاتين الحركتين.")
    if from_movement.stock_item_id != stock_item.pk or (
        to_movement.stock_item_id != stock_item.pk
    ):
        raise ValidationError("الحركتان لا تخصان هذا الرصيد.")

    existing = StockLedgerReconciliation.objects.filter(
        from_movement=from_movement, to_movement=to_movement, field=field
    ).first()
    if existing is not None:
        return existing

    return StockLedgerReconciliation.objects.create(
        stock_item=stock_item,
        field=field,
        from_movement=from_movement,
        to_movement=to_movement,
        observed_before=observed_before,
        observed_after=observed_after,
        reason=reason.strip(),
        actor=actor,
        request_id=get_request_id() or "",
    )


def unreconciled_ledger_breaks(*, sku: str | None = None) -> list[dict]:
    """Every ledger discontinuity that no reconciliation explains."""
    return [
        drift
        for drift in verify_stock_integrity(sku=sku)
        if drift["check"] == "ledger_chain"
    ]


def low_stock_report(*, sku: str | None = None) -> list[dict]:
    """Items at or below their effective low-stock threshold (FR-027).

    Informational. Low stock is a commercial fact, not a data defect, so it
    never counts as drift.
    """
    items = StockItem.objects.select_related("variant__product").order_by("variant_id")
    if sku is not None:
        items = items.filter(variant__sku=sku)

    return [
        {
            "sku": item.variant.sku,
            "product": item.variant.product.name,
            "available": item.available,
            "threshold": item.effective_low_stock_threshold,
            "state": "out_of_stock" if item.is_out_of_stock else "low_stock",
        }
        for item in items
        if item.is_out_of_stock or item.is_low_stock
    ]


def release_expired(now=None, *, batch_size: int = 500) -> int:
    """Idempotent sweeper (FR-024). A second run releases nothing."""
    now = now or timezone.now()
    released = 0
    while True:
        ids = list(
            StockReservation.objects.filter(
                state=ReservationState.ACTIVE, expires_at__lt=now
            ).values_list("pk", flat=True)[:batch_size]
        )
        if not ids:
            break
        for pk in ids:
            with transaction.atomic():
                reservation = StockReservation.objects.select_for_update().get(pk=pk)
                if reservation.state == ReservationState.ACTIVE:
                    release(reservation, expired=True)
                    released += 1
    return released
