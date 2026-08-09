"""Payments and refunds (FR-070 – FR-079, INV-004).

**No payment provider integration exists.** Verified across the whole
repository: no SDK, no credential, no endpoint, no webhook. The six methods the
storefront renders are display labels, each carrying an Arabic notice saying so.

Launch scope is cash on delivery plus manual/offline recording. The provider
boundary is built correctly now so a real gateway is a small, separate,
credential-gated increment later (FR-079) — not so that anything here pretends
to be live.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class PaymentState(models.TextChoices):
    PENDING = "pending", "قيد الانتظار"
    AUTHORISED = "authorised", "محجوز"
    CAPTURED = "captured", "محصّل"
    FAILED = "failed", "فشل"
    CANCELLED = "cancelled", "ملغي"
    PARTIALLY_REFUNDED = "partially_refunded", "مسترجع جزئيًا"
    REFUNDED = "refunded", "مسترجع"


#: payment-state-machine.md §2. Money never moves backwards into `pending`, and a
#: captured payment can never become `failed`.
ALLOWED_PAYMENT_TRANSITIONS: dict[str, frozenset[str]] = {
    PaymentState.PENDING: frozenset(
        {
            PaymentState.AUTHORISED,
            PaymentState.CAPTURED,
            PaymentState.FAILED,
            PaymentState.CANCELLED,
        }
    ),
    PaymentState.AUTHORISED: frozenset(
        {PaymentState.CAPTURED, PaymentState.CANCELLED, PaymentState.FAILED}
    ),
    PaymentState.CAPTURED: frozenset(
        {PaymentState.PARTIALLY_REFUNDED, PaymentState.REFUNDED}
    ),
    PaymentState.PARTIALLY_REFUNDED: frozenset(
        {PaymentState.PARTIALLY_REFUNDED, PaymentState.REFUNDED}
    ),
    PaymentState.FAILED: frozenset(),
    PaymentState.CANCELLED: frozenset(),
    PaymentState.REFUNDED: frozenset(),
}


class RefundState(models.TextChoices):
    PENDING = "pending", "قيد التنفيذ"
    COMPLETED = "completed", "منفّذ"
    FAILED = "failed", "فشل"


class PaymentMethod(TimeStampedModel):
    """Mirrors the six storefront options by code (FR-072)."""

    code = models.SlugField("الكود", max_length=40, unique=True)
    label = models.CharField("الاسم", max_length=80)
    description = models.CharField("الوصف", max_length=200, blank=True, default="")
    icon_path = models.CharField("الأيقونة", max_length=200, blank=True, default="")
    notice = models.CharField(
        "تنويه", max_length=255, blank=True, default="",
        help_text="يُعرض عندما تكون الطريقة غير مفعّلة بعد.",
    )
    is_active = models.BooleanField("معروضة", default=True)
    is_integrated = models.BooleanField(
        "متصلة بمزود",
        default=False,
        help_text="لا يوجد أي تكامل مع مزود دفع في هذا الإصدار.",
    )
    collects_on_delivery = models.BooleanField("تحصيل عند الاستلام", default=False)
    is_manual = models.BooleanField("تسجيل يدوي بواسطة الفريق", default=False)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "طريقة دفع"
        verbose_name_plural = "طرق الدفع"
        ordering = ["position", "code"]

    def __str__(self) -> str:
        return self.label

    @property
    def is_available_for_checkout(self) -> bool:
        """COD and manual methods work; everything else is 'coming soon'."""
        return self.is_active and (
            self.collects_on_delivery or self.is_manual or self.is_integrated
        )


class Payment(TimeStampedModel):
    order = models.ForeignKey(
        "orders.Order", on_delete=models.PROTECT, related_name="payments", verbose_name="الطلب"
    )
    method = models.ForeignKey(
        PaymentMethod, on_delete=models.PROTECT, related_name="payments", verbose_name="الطريقة"
    )
    amount = models.DecimalField(
        "المبلغ",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    currency = models.CharField("العملة", max_length=3, default="EGP")
    state = models.CharField(
        "الحالة", max_length=20, choices=PaymentState.choices, default=PaymentState.PENDING
    )
    provider_reference = models.CharField(
        "مرجع المزود", max_length=128, blank=True, default=""
    )
    idempotency_key = models.CharField(
        "مفتاح التكرار", max_length=64, null=True, blank=True, unique=True
    )
    captured_at = models.DateTimeField("حُصّل في", null=True, blank=True)
    failed_reason = models.CharField("سبب الفشل", max_length=255, blank=True, default="")
    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments",
        verbose_name="سجّله",
    )

    class Meta:
        verbose_name = "دفعة"
        verbose_name_plural = "المدفوعات"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["order", "state"], name="payment_order_state_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=Decimal("0")), name="payment_amount_positive"
            )
        ]

    def __str__(self) -> str:
        return f"{self.order.number} — {self.amount} {self.currency}"

    def can_transition_to(self, target: str) -> bool:
        return target in ALLOWED_PAYMENT_TRANSITIONS.get(self.state, frozenset())

    @property
    def refunded_amount(self) -> Decimal:
        total = self.refunds.filter(state=RefundState.COMPLETED).aggregate(
            total=models.Sum("amount")
        )["total"]
        return total or Decimal("0.00")

    @property
    def refundable_amount(self) -> Decimal:
        """Captured minus already refunded (INV-004)."""
        if self.state not in {
            PaymentState.CAPTURED,
            PaymentState.PARTIALLY_REFUNDED,
        }:
            return Decimal("0.00")
        return self.amount - self.refunded_amount


class PaymentEvent(models.Model):
    """Append-only provider event log.

    ``provider_event_id`` is unique: a replayed callback violates the constraint
    and is swallowed as a no-op rather than double-crediting an order (FR-074).
    Only a digest of the payload is stored — never a raw body, never card data
    (FR-077).
    """

    payment = models.ForeignKey(
        Payment, on_delete=models.CASCADE, related_name="events", verbose_name="الدفعة"
    )
    event_type = models.CharField("النوع", max_length=40)
    provider_event_id = models.CharField(
        "معرف حدث المزود", max_length=128, null=True, blank=True, unique=True
    )
    payload_digest = models.CharField("بصمة الحمولة", max_length=128, blank=True, default="")
    note = models.CharField("ملاحظة", max_length=255, blank=True, default="")
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "حدث دفع"
        verbose_name_plural = "أحداث الدفع"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.payment_id}: {self.event_type}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("أحداث الدفع سجل غير قابل للتعديل.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("أحداث الدفع سجل غير قابل للحذف.")


class Refund(TimeStampedModel):
    payment = models.ForeignKey(
        Payment, on_delete=models.PROTECT, related_name="refunds", verbose_name="الدفعة"
    )
    amount = models.DecimalField(
        "المبلغ",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    reason = models.CharField("السبب", max_length=255)
    state = models.CharField(
        "الحالة", max_length=16, choices=RefundState.choices, default=RefundState.PENDING
    )
    provider_reference = models.CharField(
        "مرجع المزود", max_length=128, blank=True, default=""
    )
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="refunds",
        verbose_name="المنفّذ",
    )

    class Meta:
        verbose_name = "استرجاع"
        verbose_name_plural = "الاسترجاعات"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=Decimal("0")), name="refund_amount_positive"
            )
        ]

    def __str__(self) -> str:
        return f"استرجاع {self.amount} — {self.payment.order.number}"
