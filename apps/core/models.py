"""Shared bases and the single source of commerce configuration (FR-005)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField("أنشئ في", auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField("حُدّث في", auto_now=True)

    class Meta:
        abstract = True


class PublicationStatus(models.TextChoices):
    DRAFT = "draft", "مسودة"
    PUBLISHED = "published", "منشور"
    ARCHIVED = "archived", "مؤرشف"


class PublishableQuerySet(models.QuerySet):
    """Lifecycle filters shared by every archivable model (FR-014).

    ``active`` is the default reading of the catalogue: everything that has not
    been archived, draft included. It is deliberately *not* the same as
    ``published`` — staff still work on drafts, customers never see them.
    """

    def published(self):
        return self.filter(status=PublicationStatus.PUBLISHED)

    def active(self):
        return self.exclude(status=PublicationStatus.ARCHIVED)

    def archived(self):
        return self.filter(status=PublicationStatus.ARCHIVED)


class PublishableModel(TimeStampedModel):
    """Draft / published / archived lifecycle (FR-013, FR-014).

    Archiving replaces deletion for anything an order can reference, so order
    history stays truthful after the catalogue moves on (FR-067).
    """

    status = models.CharField(
        "الحالة",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    published_at = models.DateTimeField("نُشر في", null=True, blank=True)
    archived_at = models.DateTimeField("أُرشف في", null=True, blank=True)

    class Meta:
        abstract = True

    @property
    def is_published(self) -> bool:
        return self.status == PublicationStatus.PUBLISHED


class SiteSettingManager(models.Manager):
    def get_solo(self) -> "SiteSetting":
        obj, _ = self.get_or_create(pk=1)
        return obj


class SiteSetting(TimeStampedModel):
    """Singleton holding every commerce constant (FR-005).

    Values are duplicated nowhere else: not in views, not in templates, not in
    JavaScript. Defaults mirror the approved fixture ``site`` block exactly.
    """

    vat_rate = models.DecimalField(
        "نسبة ضريبة القيمة المضافة",
        max_digits=5,
        decimal_places=4,
        default=Decimal("0.1400"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="أسعار الكتالوج شاملة الضريبة؛ تُستخرج الضريبة ولا تُضاف.",
    )
    free_shipping_threshold = models.DecimalField(
        "حد الشحن المجاني",
        max_digits=12,
        decimal_places=2,
        default=Decimal("1500.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    currency_code = models.CharField("رمز العملة", max_length=3, default="EGP")
    currency_label = models.CharField("رمز العرض", max_length=8, default="ج.م")
    currency_decimal_places = models.PositiveSmallIntegerField("خانات عشرية", default=0)

    order_number_prefix = models.CharField("بادئة رقم الطلب", max_length=8, default="ZK")
    max_line_quantity = models.PositiveSmallIntegerField(
        "أقصى كمية للسطر",
        default=9,
        help_text="يطابق حد الواجهة الحالي (1–9).",
    )
    cart_ttl_days = models.PositiveSmallIntegerField("مدة صلاحية السلة (أيام)", default=30)
    reservation_ttl_minutes = models.PositiveIntegerField(
        "مدة حجز المخزون (دقائق)", default=60
    )
    low_stock_threshold = models.PositiveIntegerField("حد المخزون المنخفض", default=5)

    prototype_notice = models.TextField("تنويه العرض", blank=True, default="")

    objects = SiteSettingManager()

    class Meta:
        verbose_name = "إعدادات المتجر"
        verbose_name_plural = "إعدادات المتجر"

    def __str__(self) -> str:
        return "إعدادات متجر زاكي"

    def clean(self) -> None:
        if self.pk not in (None, 1):
            raise ValidationError("يوجد سجل إعدادات واحد فقط.")

    def save(self, *args, **kwargs):
        # Enforce the singleton at the row level rather than by convention.
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - defensive
        raise ValidationError("لا يمكن حذف إعدادات المتجر.")

    @property
    def vat_percent(self) -> Decimal:
        return (self.vat_rate * Decimal("100")).quantize(Decimal("0.01"))
