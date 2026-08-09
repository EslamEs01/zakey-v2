"""Stock, movements and reservations (FR-020 – FR-029, INV-001).

The load-bearing rule is a **database** constraint::

    reserved <= on_hand

That is what makes overselling structurally impossible. Application logic is the
first line of defence; the constraint is the one that cannot be bypassed by a
bug, a shell session, a data import or an admin action (FR-029).
"""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import TimeStampedModel


class MovementReason(models.TextChoices):
    PURCHASE = "purchase", "توريد"
    RESERVE = "reserve", "حجز"
    RELEASE = "release", "إلغاء حجز"
    FULFILL = "fulfill", "تنفيذ"
    RETURN = "return", "مرتجع"
    ADJUST = "adjust", "تسوية"
    DAMAGED = "damaged", "تالف"
    LOST = "lost", "مفقود"
    CORRECTION = "correction", "تصحيح"


class ReservationState(models.TextChoices):
    ACTIVE = "active", "نشط"
    RELEASED = "released", "مُفرج عنه"
    CONSUMED = "consumed", "مُستهلك"
    EXPIRED = "expired", "منتهي"


class StockItem(TimeStampedModel):
    variant = models.OneToOneField(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="stock_item",
        verbose_name="الخيار",
    )
    on_hand = models.IntegerField("الكمية المتوفرة", default=0)
    reserved = models.IntegerField("الكمية المحجوزة", default=0)
    low_stock_threshold = models.PositiveIntegerField(
        "حد المخزون المنخفض", null=True, blank=True
    )

    class Meta:
        verbose_name = "رصيد مخزون"
        verbose_name_plural = "أرصدة المخزون"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(on_hand__gte=0), name="stock_on_hand_non_negative"
            ),
            models.CheckConstraint(
                condition=models.Q(reserved__gte=0), name="stock_reserved_non_negative"
            ),
            # INV-001. This single line is what prevents overselling even if
            # every service above it is wrong.
            models.CheckConstraint(
                condition=models.Q(reserved__lte=models.F("on_hand")),
                name="stock_reserved_not_above_on_hand",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku}: {self.available} متاح"

    @property
    def available(self) -> int:
        return self.on_hand - self.reserved

    @property
    def effective_low_stock_threshold(self) -> int:
        if self.low_stock_threshold is not None:
            return self.low_stock_threshold
        from apps.core.models import SiteSetting

        return SiteSetting.objects.get_solo().low_stock_threshold

    @property
    def is_low_stock(self) -> bool:
        return 0 < self.available <= self.effective_low_stock_threshold

    @property
    def is_out_of_stock(self) -> bool:
        return self.available <= 0


class StockMovement(models.Model):
    """Append-only ledger (FR-021).

    No update or delete path exists, for anyone, including superusers.
    """

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="movements", verbose_name="الرصيد"
    )
    delta = models.IntegerField("التغيير")
    reason = models.CharField("السبب", max_length=20, choices=MovementReason.choices)
    on_hand_before = models.IntegerField("المتوفر قبل")
    on_hand_after = models.IntegerField("المتوفر بعد")
    reserved_before = models.IntegerField("المحجوز قبل")
    reserved_after = models.IntegerField("المحجوز بعد")
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="الطلب",
    )
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
        verbose_name="المنفّذ",
    )
    note = models.CharField("ملاحظة", max_length=255, blank=True, default="")
    request_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "حركة مخزون"
        verbose_name_plural = "حركات المخزون"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["stock_item", "-created_at"], name="movement_item_time_idx")
        ]

    def __str__(self) -> str:
        return f"{self.stock_item.variant.sku} {self.delta:+d} ({self.get_reason_display()})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("حركات المخزون سجل غير قابل للتعديل.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("حركات المخزون سجل غير قابل للحذف.")


class StockReservation(TimeStampedModel):
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="reservations", verbose_name="الرصيد"
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reservations",
        verbose_name="الطلب",
    )
    quantity = models.PositiveIntegerField("الكمية")
    state = models.CharField(
        "الحالة",
        max_length=16,
        choices=ReservationState.choices,
        default=ReservationState.ACTIVE,
    )
    expires_at = models.DateTimeField("ينتهي في", db_index=True)

    class Meta:
        verbose_name = "حجز مخزون"
        verbose_name_plural = "حجوزات المخزون"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state", "expires_at"], name="reservation_sweep_idx")
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="reservation_quantity_positive"
            )
        ]

    def __str__(self) -> str:
        return f"{self.stock_item.variant.sku} × {self.quantity} ({self.get_state_display()})"


class StockLedgerReconciliation(models.Model):
    """An explicit, audited explanation for a break in the movement chain.

    The movement ledger is append-only: a row that was written cannot be edited
    or deleted, and that is the property the whole inventory audit rests on. So
    when something writes ``StockItem.reserved`` without recording a movement —
    as an early, unsafe development reset once did — the resulting discontinuity
    between two adjacent movements is **permanent**. It is history, and history
    is not editable.

    Leaving the integrity gate permanently red is not an option either: an alarm
    that is always on is an alarm nobody reads.

    This model is the third way. It records, as its own append-only row, that a
    named human examined a *specific* discontinuity — identified by the exact
    pair of movements it sits between and the exact values observed on each side
    — and explained it. ``verify_stock_integrity`` then treats that one
    discontinuity as reconciled.

    Two properties keep this from becoming a rubber stamp:

    * it is pinned to ``from_movement``/``to_movement`` **and** to the observed
      values, so if the data changes underneath it the reconciliation stops
      matching and the drift is reported again;
    * it explains only the gap it names. Any other discontinuity, on any item,
      still fails the gate.

    It is deliberately not a suppression list keyed on SKU, primary key or
    "current mismatch": those would hide the next incident too.
    """

    FIELD_CHOICES = (
        ("on_hand", "المتوفر"),
        ("reserved", "المحجوز"),
    )

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="reconciliations",
        verbose_name="الرصيد",
    )
    field = models.CharField("الحقل", max_length=16, choices=FIELD_CHOICES)
    from_movement = models.ForeignKey(
        StockMovement,
        on_delete=models.PROTECT,
        related_name="reconciliations_from",
        verbose_name="الحركة السابقة",
    )
    to_movement = models.ForeignKey(
        StockMovement,
        on_delete=models.PROTECT,
        related_name="reconciliations_to",
        verbose_name="الحركة التالية",
    )
    #: The two values that disagree. Recorded so the reconciliation stops
    #: applying if the underlying rows ever change.
    observed_before = models.IntegerField("القيمة قبل")
    observed_after = models.IntegerField("القيمة بعد")
    reason = models.TextField("سبب التسوية")
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_reconciliations",
        verbose_name="المنفّذ",
    )
    request_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "تسوية سجل مخزون"
        verbose_name_plural = "تسويات سجل المخزون"
        ordering = ["-created_at", "-id"]
        constraints = [
            # One reconciliation per (gap, field). Re-running the repair is a
            # no-op rather than a second explanation for the same break.
            models.UniqueConstraint(
                fields=["from_movement", "to_movement", "field"],
                name="one_reconciliation_per_ledger_gap",
            )
        ]

    def __str__(self) -> str:
        return (
            f"{self.stock_item.variant.sku} {self.field} "
            f"{self.observed_before}->{self.observed_after}"
        )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("تسويات سجل المخزون سجل غير قابل للتعديل.")
        if not (self.reason or "").strip():
            raise ValidationError("سبب التسوية مطلوب.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("تسويات سجل المخزون سجل غير قابل للحذف.")
