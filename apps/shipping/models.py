"""Egyptian geography, shipping and installation (FR-044 – FR-049).

Geography keys are the ones the approved storefront already uses, so addresses,
eligibility and URLs keep working unchanged (frontend-contract.md §2).

Shipping and installation *prices* do not exist anywhere in the approved
frontend: ``shippingOptions`` carry label/description/eligibility/icon and no
price field at all. Rates are therefore staff-configurable and seeded with
clearly-labelled development placeholders (ASM-004, ASM-005).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


class Governorate(TimeStampedModel):
    """One of the 27 Egyptian governorates."""

    key = models.SlugField("المفتاح", max_length=40, unique=True)
    name = models.CharField("المحافظة", max_length=80)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّلة", default=True)

    class Meta:
        verbose_name = "محافظة"
        verbose_name_plural = "المحافظات"
        ordering = ["position", "key"]

    def __str__(self) -> str:
        return self.name


class ServiceArea(TimeStampedModel):
    """A named area inside a governorate, carrying service eligibility."""

    key = models.SlugField("المفتاح", max_length=60, unique=True)
    governorate = models.ForeignKey(
        Governorate, on_delete=models.CASCADE, related_name="areas"
    )
    name = models.CharField("المنطقة", max_length=80)
    same_day_eligible = models.BooleanField("يدعم التوصيل في اليوم نفسه", default=False)
    installation_eligible = models.BooleanField("يدعم التركيب", default=False)
    is_active = models.BooleanField("مفعّلة", default=True)

    class Meta:
        verbose_name = "منطقة خدمة"
        verbose_name_plural = "مناطق الخدمة"
        ordering = ["governorate__position", "name"]

    def __str__(self) -> str:
        return f"{self.name} — {self.governorate.name}"


class ShippingZone(TimeStampedModel):
    name = models.CharField("اسم النطاق", max_length=80, unique=True)
    governorates = models.ManyToManyField(
        Governorate, related_name="zones", blank=True, verbose_name="المحافظات"
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "نطاق شحن"
        verbose_name_plural = "نطاقات الشحن"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class ShippingMethod(TimeStampedModel):
    """Mirrors the three approved storefront options by code."""

    code = models.SlugField("الكود", max_length=40, unique=True)
    label = models.CharField("الاسم", max_length=80)
    description = models.CharField("الوصف", max_length=200, blank=True, default="")
    icon_path = models.CharField("الأيقونة", max_length=200, blank=True, default="")
    requires_area_eligibility = models.BooleanField(
        "يتطلب منطقة مؤهلة",
        default=False,
        help_text="مثل التوصيل في اليوم نفسه داخل مناطق محددة.",
    )
    free_over_threshold = models.BooleanField(
        "مجاني فوق حد الشحن المجاني",
        default=False,
        help_text="يُطبَّق على الإجمالي بعد الخصم.",
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّلة", default=True)

    class Meta:
        verbose_name = "طريقة شحن"
        verbose_name_plural = "طرق الشحن"
        ordering = ["position", "code"]

    def __str__(self) -> str:
        return self.label


class ShippingRate(TimeStampedModel):
    """Price of one method within one zone (FR-045).

    ``is_placeholder`` marks development values that are NOT commercially
    approved. Production refuses to quote a placeholder (ASM-004).
    """

    method = models.ForeignKey(
        ShippingMethod, on_delete=models.CASCADE, related_name="rates"
    )
    zone = models.ForeignKey(
        ShippingZone, on_delete=models.CASCADE, related_name="rates"
    )
    price = models.DecimalField(
        "السعر",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    estimated_delivery_text = models.CharField(
        "المدة المتوقعة", max_length=120, blank=True, default=""
    )
    is_placeholder = models.BooleanField(
        "قيمة تطويرية غير معتمدة",
        default=True,
        help_text="سعر تجريبي للتطوير فقط ولا يمثل سعرًا تجاريًا معتمدًا.",
    )
    free_threshold_only = models.BooleanField(
        "مجاني فوق الحد فقط",
        default=False,
        help_text=(
            "لا تُعرض هذه الطريقة إلا عندما يبلغ إجمالي الطلب حد الشحن المجاني، "
            "ولا يوجد سعر مدفوع تحت الحد. حالة الإطلاق المعتمدة."
        ),
    )
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "سعر شحن"
        verbose_name_plural = "أسعار الشحن"
        ordering = ["method__position", "zone__position"]
        constraints = [
            models.UniqueConstraint(
                fields=["method", "zone"], name="unique_rate_per_method_zone"
            ),
            models.CheckConstraint(
                condition=models.Q(price__gte=Decimal("0")),
                name="shipping_rate_price_non_negative",
            ),
            # A free-above-threshold rate that also carries a price is a
            # contradiction the launch policy must not be able to express: it
            # would let a paid amount reappear below the threshold through a
            # single careless admin edit.
            models.CheckConstraint(
                condition=(
                    models.Q(free_threshold_only=False) | models.Q(price=Decimal("0"))
                ),
                name="free_threshold_only_rate_is_free",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.method.label} — {self.zone.name}"


class InstallationService(TimeStampedModel):
    """Optional installation, offered only where eligible (FR-048)."""

    name = models.CharField("اسم الخدمة", max_length=80, default="خدمة التركيب")
    fee = models.DecimalField(
        "الرسوم",
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    governorates = models.ManyToManyField(
        Governorate,
        related_name="installation_services",
        blank=True,
        verbose_name="المحافظات المؤهلة",
    )
    is_placeholder = models.BooleanField(
        "قيمة تطويرية غير معتمدة",
        default=True,
        help_text="رسوم تجريبية للتطوير فقط ولا تمثل سعرًا تجاريًا معتمدًا.",
    )
    is_active = models.BooleanField("مفعّلة", default=True)

    class Meta:
        verbose_name = "خدمة تركيب"
        verbose_name_plural = "خدمات التركيب"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fee__gte=Decimal("0")),
                name="installation_fee_non_negative",
            )
        ]

    def __str__(self) -> str:
        return self.name
