"""Customer reviews (FR-090 – FR-095)."""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.i18n import TranslatableModel

from apps.core.models import TimeStampedModel


class ReviewStatus(models.TextChoices):
    PENDING = "pending", "قيد المراجعة"
    APPROVED = "approved", "منشور"
    REJECTED = "rejected", "مرفوض"


class ReviewQuerySet(models.QuerySet):
    def approved(self) -> "ReviewQuerySet":
        return self.filter(status=ReviewStatus.APPROVED)


class Review(TranslatableModel, TimeStampedModel):
    translatable_fields = ("author_name", "title", "body",)

    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    product = models.ForeignKey(
        "catalog.Product", on_delete=models.CASCADE, related_name="reviews", verbose_name="المنتج"
    )
    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviews",
        verbose_name="العميل",
    )
    author_name = models.CharField("اسم الكاتب", max_length=120)
    author_name_en = models.CharField(
        "اسم الكاتب (إنجليزي)", max_length=120, blank=True, default=""
    )
    rating = models.PositiveSmallIntegerField(
        "التقييم", validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField("العنوان", max_length=160, blank=True, default="")
    title_en = models.CharField(
        "العنوان (إنجليزي)", max_length=160, blank=True, default=""
    )
    body = models.TextField("النص")
    body_en = models.TextField("النص (إنجليزي)", blank=True, default="")
    status = models.CharField(
        "الحالة", max_length=16, choices=ReviewStatus.choices, default=ReviewStatus.PENDING
    )
    is_verified_purchase = models.BooleanField("شراء موثّق", default=False)
    staff_response = models.TextField("رد الفريق", blank=True, default="")
    placement = models.JSONField(
        "أماكن العرض",
        default=list,
        blank=True,
        help_text='مثل ["product", "home"] كما في بيانات الواجهة.',
    )
    moderated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="moderated_reviews",
        verbose_name="راجعه",
    )
    moderated_at = models.DateTimeField("روجع في", null=True, blank=True)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        verbose_name = "تقييم"
        verbose_name_plural = "التقييمات"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["product", "status"], name="review_product_status_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(rating__gte=1) & models.Q(rating__lte=5),
                name="review_rating_between_1_and_5",
            ),
            # One review per customer per product (FR-093); anonymous imported
            # demo reviews have no customer and are exempt.
            models.UniqueConstraint(
                fields=["product", "customer"],
                condition=models.Q(customer__isnull=False),
                name="unique_review_per_customer_product",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.rating}/5"
