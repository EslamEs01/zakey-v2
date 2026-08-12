"""Coupons (FR-080 – FR-086, INV-005).

Codes are stored uppercase because the storefront uppercases input before
comparing (``static/src/js/pages/cart.js:141``), so matching stays consistent.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.i18n import TranslatableModel

from apps.core.models import TimeStampedModel


class DiscountType(models.TextChoices):
    PERCENTAGE = "percentage", "نسبة مئوية"
    FIXED = "fixed", "مبلغ ثابت"


class Coupon(TranslatableModel, TimeStampedModel):
    translatable_fields = ("description",)

    code = models.CharField("الكود", max_length=32, unique=True)
    description = models.CharField("الوصف", max_length=200, blank=True, default="")
    description_en = models.CharField(
        "الوصف (إنجليزي)", max_length=200, blank=True, default=""
    )
    discount_type = models.CharField(
        "نوع الخصم",
        max_length=16,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
    )
    value = models.DecimalField(
        "القيمة",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="نسبة مئوية (مثل 5) أو مبلغ ثابت بالجنيه.",
    )
    max_discount = models.DecimalField(
        "أقصى خصم",
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="سقف اختياري للخصم النسبي.",
    )
    starts_at = models.DateTimeField("يبدأ في", null=True, blank=True)
    ends_at = models.DateTimeField("ينتهي في", null=True, blank=True)
    usage_limit = models.PositiveIntegerField("حد الاستخدام الكلي", null=True, blank=True)
    per_customer_limit = models.PositiveIntegerField(
        "حد الاستخدام لكل عميل", null=True, blank=True
    )
    minimum_subtotal = models.DecimalField(
        "أقل إجمالي مطلوب", max_digits=12, decimal_places=2, null=True, blank=True
    )
    products = models.ManyToManyField(
        "catalog.Product", blank=True, related_name="coupons", verbose_name="منتجات محددة"
    )
    categories = models.ManyToManyField(
        "catalog.Category", blank=True, related_name="coupons", verbose_name="تصنيفات محددة"
    )
    times_used = models.PositiveIntegerField("عدد مرات الاستخدام", default=0)
    is_active = models.BooleanField("مفعّل", default=True)
    is_demo = models.BooleanField(
        "كود عرض تجريبي",
        default=False,
        help_text="لا يمثل عرضًا تجاريًا حقيقيًا؛ للتطوير فقط.",
    )

    class Meta:
        verbose_name = "كود خصم"
        verbose_name_plural = "أكواد الخصم"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(value__gt=Decimal("0")), name="coupon_value_positive"
            ),
            models.CheckConstraint(
                condition=models.Q(ends_at__isnull=True)
                | models.Q(starts_at__isnull=True)
                | models.Q(ends_at__gt=models.F("starts_at")),
                name="coupon_window_ordered",
            ),
            # INV-005 at the database level.
            models.CheckConstraint(
                condition=models.Q(usage_limit__isnull=True)
                | models.Q(times_used__lte=models.F("usage_limit")),
                name="coupon_usage_within_limit",
            ),
        ]

    def __str__(self) -> str:
        return self.code

    def clean(self) -> None:
        if self.discount_type == DiscountType.PERCENTAGE and self.value > Decimal("100"):
            raise ValidationError({"value": "النسبة المئوية لا يمكن أن تتجاوز 100."})

    def save(self, *args, **kwargs):
        if self.code:
            self.code = self.code.strip().upper()
        super().save(*args, **kwargs)


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(
        Coupon, on_delete=models.PROTECT, related_name="redemptions", verbose_name="الكود"
    )
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="coupon_redemptions",
        verbose_name="الطلب",
    )
    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coupon_redemptions",
        verbose_name="العميل",
    )
    amount = models.DecimalField("قيمة الخصم", max_digits=12, decimal_places=2)
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "استخدام كود"
        verbose_name_plural = "استخدامات الأكواد"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["coupon", "order"], name="unique_coupon_per_order"
            )
        ]

    def __str__(self) -> str:
        return f"{self.coupon.code} — {self.order.number}"
