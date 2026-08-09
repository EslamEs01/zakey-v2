"""Orders (FR-060 – FR-069, INV-002, INV-003, INV-006, INV-007).

Orders are **snapshots**. Product names, SKUs, prices, the address and every
money component are copied at creation and never change afterwards, so history
stays truthful when the catalogue is renamed, repriced or archived (FR-067).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class OrderStatus(models.TextChoices):
    PENDING = "pending", "قيد الانتظار"
    CONFIRMED = "confirmed", "مؤكد"
    PROCESSING = "processing", "قيد التجهيز"
    SHIPPED = "shipped", "تم الشحن"
    DELIVERED = "delivered", "تم التسليم"
    CANCELLED = "cancelled", "ملغي"
    REFUNDED = "refunded", "مسترجع"


#: The authoritative transition matrix (order-state-machine.md §1).
#: Every pair NOT listed here is rejected, including all backward moves, all
#: skips, and every transition out of a terminal state.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.CONFIRMED, OrderStatus.CANCELLED}),
    OrderStatus.CONFIRMED: frozenset({OrderStatus.PROCESSING, OrderStatus.CANCELLED}),
    OrderStatus.PROCESSING: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DELIVERED, OrderStatus.CANCELLED}),
    OrderStatus.DELIVERED: frozenset({OrderStatus.REFUNDED}),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REFUNDED: frozenset(),
}

TERMINAL_STATUSES = frozenset(
    {OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REFUNDED}
)


class PaymentStatus(models.TextChoices):
    UNPAID = "unpaid", "غير مدفوع"
    PARTIALLY_PAID = "partially_paid", "مدفوع جزئيًا"
    PAID = "paid", "مدفوع"
    PARTIALLY_REFUNDED = "partially_refunded", "مسترجع جزئيًا"
    REFUNDED = "refunded", "مسترجع بالكامل"
    FAILED = "failed", "فشل"
    CANCELLED = "cancelled", "ملغي"


class FulfillmentStatus(models.TextChoices):
    UNFULFILLED = "unfulfilled", "لم يُجهّز"
    PARTIALLY_FULFILLED = "partially_fulfilled", "مجهّز جزئيًا"
    FULFILLED = "fulfilled", "مجهّز"
    RETURNED = "returned", "مرتجع"


class InvalidTransition(ValidationError):
    def __init__(self, current: str, target: str):
        self.current, self.target = current, target
        allowed = ", ".join(sorted(ALLOWED_TRANSITIONS.get(current, frozenset()))) or "لا شيء"
        super().__init__(
            f"انتقال غير مسموح من «{current}» إلى «{target}». المسموح: {allowed}."
        )


class Order(TimeStampedModel):
    number = models.CharField("رقم الطلب", max_length=32, unique=True)
    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="العميل",
    )
    email = models.EmailField("البريد الإلكتروني")
    phone = models.CharField("رقم الموبايل", max_length=16)

    status = models.CharField(
        "الحالة", max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING
    )
    payment_status = models.CharField(
        "حالة الدفع",
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    fulfillment_status = models.CharField(
        "حالة التجهيز",
        max_length=24,
        choices=FulfillmentStatus.choices,
        default=FulfillmentStatus.UNFULFILLED,
    )

    # INV-002: one confirmed order per key. A replayed POST returns the original.
    idempotency_key = models.CharField("مفتاح التكرار", max_length=64, unique=True)

    # --- money snapshots (immutable after creation, INV-003) ----------------
    subtotal = models.DecimalField("الإجمالي الفرعي", max_digits=12, decimal_places=2)
    discount_total = models.DecimalField(
        "الخصم", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    coupon_code = models.CharField("كود الخصم", max_length=32, blank=True, default="")
    shipping_method_label = models.CharField(
        "طريقة الشحن", max_length=80, blank=True, default=""
    )
    shipping_total = models.DecimalField(
        "تكلفة الشحن", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    installation_requested = models.BooleanField("طلب التركيب", default=False)
    installation_total = models.DecimalField(
        "تكلفة التركيب", max_digits=12, decimal_places=2, default=Decimal("0.00")
    )
    vat_amount = models.DecimalField(
        "ضريبة القيمة المضافة (مستخرجة)",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="مستخرجة من الإجمالي الشامل ولا تُضاف إليه.",
    )
    vat_rate = models.DecimalField(
        "نسبة الضريبة وقت الطلب", max_digits=5, decimal_places=4, default=Decimal("0.1400")
    )
    grand_total = models.DecimalField("الإجمالي", max_digits=12, decimal_places=2)

    used_placeholder_rates = models.BooleanField(
        "استخدم أسعارًا تطويرية",
        default=False,
        help_text="سجل تدقيق: أُنشئ الطلب بأسعار شحن/تركيب غير معتمدة تجاريًا.",
    )

    terms_accepted_at = models.DateTimeField("قبل الشروط في", null=True, blank=True)
    placed_at = models.DateTimeField("أنشئ في", null=True, blank=True, db_index=True)
    cancelled_at = models.DateTimeField("ألغي في", null=True, blank=True)
    tracking_number = models.CharField("رقم التتبع", max_length=80, blank=True, default="")

    class Meta:
        verbose_name = "طلب"
        verbose_name_plural = "الطلبات"
        ordering = ["-placed_at", "-id"]
        indexes = [
            models.Index(fields=["status", "-placed_at"], name="order_status_placed_idx"),
            models.Index(fields=["customer", "-placed_at"], name="order_customer_idx"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(grand_total__gte=Decimal("0")),
                name="order_grand_total_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=Decimal("0")),
                name="order_subtotal_non_negative",
            ),
            models.CheckConstraint(
                condition=models.Q(discount_total__gte=Decimal("0")),
                name="order_discount_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return self.number

    # -- transitions ---------------------------------------------------------

    def can_transition_to(self, target: str) -> bool:
        return target in ALLOWED_TRANSITIONS.get(self.status, frozenset())

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def allowed_next_statuses(self) -> frozenset[str]:
        return ALLOWED_TRANSITIONS.get(self.status, frozenset())

    @property
    def customer_can_cancel(self) -> bool:
        return self.status in {OrderStatus.PENDING, OrderStatus.CONFIRMED}


class OrderLine(models.Model):
    """Immutable snapshot of one purchased line (INV-003).

    Every displayed value is stored here rather than read through the FK, so a
    line renders correctly no matter what later happens to the catalogue.

    ``variant`` is PROTECT, not SET_NULL (FR-014, FR-109). Archiving a product
    never touches this column — archiving is a status change, not a delete — so
    protecting it costs the catalogue nothing. What it buys is that a *deletion*
    of something a customer actually bought is refused outright instead of
    silently blanking the reference and leaving an order that no longer points
    at what was sold. The column stays nullable for legacy rows written before
    the guard existed.
    """

    order = models.ForeignKey(
        Order, on_delete=models.PROTECT, related_name="lines", verbose_name="الطلب"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="order_lines",
        verbose_name="الخيار",
    )
    product_name = models.CharField("اسم المنتج", max_length=160)
    product_slug = models.SlugField("معرف المنتج", max_length=120, blank=True, default="")
    variant_label = models.CharField("الخيار", max_length=80, blank=True, default="")
    sku = models.CharField("SKU", max_length=64)
    image_path = models.CharField("مسار الصورة", max_length=255, blank=True, default="")
    unit_price = models.DecimalField(
        "سعر الوحدة", max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    quantity = models.PositiveSmallIntegerField("الكمية")
    line_total = models.DecimalField("إجمالي السطر", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "سطر طلب"
        verbose_name_plural = "أسطر الطلبات"
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0), name="order_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=Decimal("0")),
                name="order_line_unit_price_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product_name} × {self.quantity}"

    def save(self, *args, **kwargs):
        # Snapshots never change after creation (INV-003). Only the nullable
        # variant back-reference may be cleared by archival.
        if self.pk is not None:
            allowed = {"variant", "variant_id"}
            update_fields = set(kwargs.get("update_fields") or [])
            if not update_fields or not update_fields.issubset(allowed):
                raise ValidationError("لا يمكن تعديل سطر طلب بعد إنشائه.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("لا يمكن حذف سطر طلب.")


class OrderAddress(models.Model):
    """Address snapshot, not a foreign key (FR-067)."""

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name="address", verbose_name="الطلب"
    )
    full_name = models.CharField("الاسم", max_length=120)
    phone = models.CharField("الموبايل", max_length=16)
    governorate_key = models.CharField("مفتاح المحافظة", max_length=40)
    governorate_name = models.CharField("المحافظة", max_length=80)
    area_key = models.CharField("مفتاح المنطقة", max_length=60, blank=True, default="")
    area_name = models.CharField("المنطقة", max_length=80, blank=True, default="")
    city = models.CharField("المدينة", max_length=80)
    street = models.CharField("الشارع", max_length=140)
    building = models.CharField("المبنى", max_length=24)
    landmark = models.CharField("علامة مميزة", max_length=100, blank=True, default="")

    class Meta:
        verbose_name = "عنوان طلب"
        verbose_name_plural = "عناوين الطلبات"

    def __str__(self) -> str:
        return f"{self.governorate_name} — {self.city}"


class OrderEvent(models.Model):
    """Append-only order history (FR-069)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="events", verbose_name="الطلب"
    )
    event_type = models.CharField("النوع", max_length=40)
    from_status = models.CharField("من حالة", max_length=16, blank=True, default="")
    to_status = models.CharField("إلى حالة", max_length=16, blank=True, default="")
    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_events",
        verbose_name="المنفّذ",
    )
    note = models.CharField("ملاحظة", max_length=255, blank=True, default="")
    request_id = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "حدث طلب"
        verbose_name_plural = "أحداث الطلبات"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.order.number}: {self.event_type}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("أحداث الطلب سجل غير قابل للتعديل.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("أحداث الطلب سجل غير قابل للحذف.")


class OrderNote(TimeStampedModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="notes", verbose_name="الطلب"
    )
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_notes",
        verbose_name="الكاتب",
    )
    body = models.TextField("النص")
    is_customer_visible = models.BooleanField("مرئية للعميل", default=False)

    class Meta:
        verbose_name = "ملاحظة طلب"
        verbose_name_plural = "ملاحظات الطلبات"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.order.number}: {self.body[:40]}"
