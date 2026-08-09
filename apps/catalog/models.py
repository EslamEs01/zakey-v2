"""Catalogue (FR-010 – FR-019).

Field names and enumerations mirror the approved storefront contract so the
templates keep working: every slug, every ordering rule and the
``available | limited | unavailable`` availability vocabulary are preserved
(frontend-contract.md §2).

Prices live on the **variant** (FR-017) and are **VAT-inclusive** (FR-040).
"""

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from apps.core.uploads import validate_document_upload, validate_image_upload
from apps.core.models import (
    PublicationStatus,
    PublishableModel,
    PublishableQuerySet,
    TimeStampedModel,
)


class Availability(models.TextChoices):
    """Exactly the values the storefront filters on.

    ``fixture_provider.py:183-190`` treats ``available`` as matching both
    ``available`` and ``limited``; the selectors reproduce that.
    """

    AVAILABLE = "available", "متاح"
    LIMITED = "limited", "كمية محدودة"
    UNAVAILABLE = "unavailable", "غير متاح"


class Category(PublishableModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="التصنيف الأعلى",
    )
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    slug = models.SlugField("المعرف", max_length=80, unique=True)
    name = models.CharField("الاسم", max_length=120)
    description = models.TextField("الوصف", blank=True, default="")
    kind = models.CharField("النوع", max_length=40, blank=True, default="")
    image = models.ImageField(
        "الصورة", upload_to="categories/", blank=True, null=True,
        validators=[validate_image_upload],
    )
    legacy_image_path = models.CharField(max_length=255, blank=True, default="")
    # The category card renders a fixed-ratio image, so alt/width/height are
    # part of the rendering contract, not decoration (frontend-contract §3).
    image_alt = models.CharField("النص البديل", max_length=200, blank=True, default="")
    image_width = models.PositiveIntegerField("العرض", default=0)
    image_height = models.PositiveIntegerField("الارتفاع", default=0)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    seo_title = models.CharField("عنوان SEO", max_length=160, blank=True, default="")
    seo_description = models.CharField("وصف SEO", max_length=255, blank=True, default="")

    objects = PublishableQuerySet.as_manager()

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def image_src(self) -> str:
        """Prefer an uploaded file, fall back to the imported static path."""
        if self.image:
            return self.image.url
        return self.legacy_image_path


class Brand(TimeStampedModel):
    slug = models.SlugField("المعرف", max_length=80, unique=True)
    name = models.CharField("الاسم", max_length=120)
    logo = models.ImageField(
        "الشعار", upload_to="brands/", blank=True, null=True,
        validators=[validate_image_upload],
    )

    class Meta:
        verbose_name = "علامة تجارية"
        verbose_name_plural = "العلامات التجارية"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Collection(PublishableModel):
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    slug = models.SlugField("المعرف", max_length=80, unique=True)
    name = models.CharField("الاسم", max_length=120)
    description = models.TextField("الوصف", blank=True, default="")
    promotion_eyebrow = models.CharField("عنوان فرعي", max_length=80, blank=True, default="")
    promotion_tone = models.CharField("النغمة", max_length=40, blank=True, default="")
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    products = models.ManyToManyField(
        "catalog.Product",
        through="catalog.CollectionProduct",
        related_name="collections",
        verbose_name="المنتجات",
        blank=True,
    )

    objects = PublishableQuerySet.as_manager()

    class Meta:
        verbose_name = "مجموعة"
        verbose_name_plural = "المجموعات"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class CollectionProduct(models.Model):
    """Through model so fixture collection ordering survives (FR-016)."""

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    product = models.ForeignKey("catalog.Product", on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "منتج داخل مجموعة"
        verbose_name_plural = "منتجات المجموعات"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "product"], name="unique_product_per_collection"
            )
        ]


class ProductQuerySet(PublishableQuerySet):
    """Product lifecycle filters plus the bounded catalogue prefetch.

    ``published``/``active``/``archived`` come from :class:`PublishableQuerySet`
    so every archivable model answers the same question the same way (FR-014).
    """

    def with_catalogue_data(self) -> "ProductQuerySet":
        """Bounded query for list views (NFR-002)."""
        return self.select_related("category", "brand").prefetch_related(
            "images", "features", "variants__stock_item"
        )


class Product(PublishableModel):
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    slug = models.SlugField("المعرف", max_length=120, unique=True)
    name = models.CharField("الاسم", max_length=160)
    short_description = models.CharField("وصف مختصر", max_length=255, blank=True, default="")
    description = models.TextField("الوصف", blank=True, default="")
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, related_name="products", verbose_name="التصنيف"
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products",
        verbose_name="العلامة التجارية",
    )
    badge = models.CharField("الشارة", max_length=60, blank=True, default="")
    instalment_message = models.CharField(
        "رسالة التقسيط", max_length=255, blank=True, default=""
    )
    same_day_supported = models.BooleanField("يدعم التوصيل في اليوم نفسه", default=False)
    installation_supported = models.BooleanField("يدعم التركيب", default=False)

    # System-maintained; never hand-edited (FR-094).
    rating_average = models.DecimalField(
        "متوسط التقييم", max_digits=3, decimal_places=2, default=Decimal("0.00")
    )
    review_count = models.PositiveIntegerField("عدد التقييمات", default=0)

    seo_title = models.CharField("عنوان SEO", max_length=160, blank=True, default="")
    seo_description = models.CharField("وصف SEO", max_length=255, blank=True, default="")
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    related_products = models.ManyToManyField(
        "self",
        through="catalog.ProductRelation",
        symmetrical=False,
        related_name="related_to",
        blank=True,
        verbose_name="منتجات ذات صلة",
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = "منتج"
        verbose_name_plural = "المنتجات"
        ordering = ["position", "id"]
        indexes = [
            models.Index(fields=["status", "published_at"], name="product_status_pub_idx"),
            models.Index(fields=["category", "status"], name="product_category_idx"),
        ]

    def __str__(self) -> str:
        return self.name

    # -- derived ------------------------------------------------------------

    @property
    def default_variant(self) -> "ProductVariant | None":
        variants = list(self.variants.all())
        if not variants:
            return None
        for variant in variants:
            if variant.is_default:
                return variant
        return variants[0]

    @property
    def display_price(self) -> Decimal | None:
        variant = self.default_variant
        return variant.price if variant else None

    @property
    def compare_at_price(self) -> Decimal | None:
        variant = self.default_variant
        return variant.compare_at_price if variant else None

    @property
    def primary_image(self) -> "ProductImage | None":
        return next(iter(self.images.all()), None)

    @property
    def availability(self) -> str:
        """Derived from stock, never stored free-hand (FR-018).

        ``limited`` is reported when every in-stock variant is at or below its
        own low-stock threshold, matching how the storefront badges scarcity.

        The comparison is deliberately per-variant. Summing availability across
        finishes and comparing the total to a per-variant threshold mixes units:
        a product with four nearly-empty finishes (2 each) would total 8, clear a
        threshold of 5, and be badged "available" precisely when it is scarcest.
        Scarcity is a property of the thing a customer actually buys — one
        finish — so each is judged against its own threshold.
        """
        variants = [v for v in self.variants.all() if v.is_active]
        if not variants:
            return Availability.UNAVAILABLE

        in_stock = []
        for variant in variants:
            stock = getattr(variant, "stock_item", None)
            if stock is not None and stock.available > 0:
                in_stock.append(stock)

        if not in_stock:
            return Availability.UNAVAILABLE
        if all(
            stock.available <= stock.effective_low_stock_threshold for stock in in_stock
        ):
            return Availability.LIMITED
        return Availability.AVAILABLE

    @property
    def is_purchasable(self) -> bool:
        return self.is_published and self.availability != Availability.UNAVAILABLE


class ProductVariant(TimeStampedModel):
    """The finish axis (FR-017).

    The approved storefront has exactly one option dimension: ``finishes``
    (``{id, label, swatch}``), selected by ``<input name="finish">`` on the
    product page. Price and SKU live here so per-finish pricing is possible
    without a schema change.
    """

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="variants", verbose_name="المنتج"
    )
    sku = models.CharField("SKU", max_length=64, unique=True)
    finish_id = models.CharField("معرف اللون", max_length=64, blank=True, default="")
    finish_label = models.CharField("اللون", max_length=80, blank=True, default="")
    swatch_hex = models.CharField("لون العينة", max_length=9, blank=True, default="")
    price = models.DecimalField(
        "السعر (شامل الضريبة)",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    compare_at_price = models.DecimalField(
        "السعر قبل الخصم", max_digits=12, decimal_places=2, null=True, blank=True
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_default = models.BooleanField("افتراضي", default=False)
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "خيار منتج"
        verbose_name_plural = "خيارات المنتجات"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["sku"], name="unique_variant_sku"),
            models.UniqueConstraint(
                fields=["product"],
                condition=models.Q(is_default=True),
                name="unique_default_variant_per_product",
            ),
            models.CheckConstraint(
                condition=models.Q(price__gt=Decimal("0")),
                name="variant_price_positive",
            ),
            models.CheckConstraint(
                condition=models.Q(compare_at_price__isnull=True)
                | models.Q(compare_at_price__gt=models.F("price")),
                name="variant_compare_at_price_above_price",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.product.name} — {self.finish_label or self.sku}"


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="images", verbose_name="المنتج"
    )
    legacy_id = models.CharField(max_length=64, blank=True, default="")
    image = models.ImageField(
        "الصورة", upload_to="products/", blank=True, null=True,
        validators=[validate_image_upload],
    )
    legacy_path = models.CharField(
        "المسار الأصلي",
        max_length=255,
        blank=True,
        default="",
        help_text="مسار الأصل داخل static؛ يحافظ على ثبات الاستيراد.",
    )
    alt = models.CharField("النص البديل", max_length=200)
    width = models.PositiveIntegerField("العرض", default=0)
    height = models.PositiveIntegerField("الارتفاع", default=0)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "صورة منتج"
        verbose_name_plural = "صور المنتجات"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.alt or self.legacy_path

    @property
    def src(self) -> str:
        """Prefer an uploaded file, fall back to the imported static path."""
        if self.image:
            return self.image.url
        return self.legacy_path


class ProductFeature(TimeStampedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="features", verbose_name="المنتج"
    )
    key = models.SlugField("المفتاح", max_length=60, db_index=True)
    label = models.CharField("الاسم", max_length=120)
    description = models.CharField("الوصف", max_length=255, blank=True, default="")
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "ميزة"
        verbose_name_plural = "المميزات"
        ordering = ["position", "id"]
        indexes = [models.Index(fields=["key"], name="feature_key_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "key"], name="unique_feature_key_per_product"
            )
        ]

    def __str__(self) -> str:
        return self.label


class SpecificationGroup(TimeStampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="specification_groups",
        verbose_name="المنتج",
    )
    legacy_id = models.CharField(max_length=64, blank=True, default="")
    label = models.CharField("المجموعة", max_length=120)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "مجموعة مواصفات"
        verbose_name_plural = "مجموعات المواصفات"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.label


class SpecificationItem(models.Model):
    group = models.ForeignKey(
        SpecificationGroup,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="المجموعة",
    )
    label = models.CharField("البند", max_length=120)
    value = models.CharField("القيمة", max_length=255)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "مواصفة"
        verbose_name_plural = "المواصفات"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return f"{self.label}: {self.value}"


class ProductDocument(TimeStampedModel):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="documents", verbose_name="المنتج"
    )
    legacy_id = models.CharField(max_length=64, blank=True, default="")
    label = models.CharField("الاسم", max_length=120)
    file = models.FileField(
        "الملف", upload_to="documents/", blank=True, null=True,
        validators=[validate_document_upload],
    )
    legacy_path = models.CharField(max_length=255, blank=True, default="")
    file_format = models.CharField("الصيغة", max_length=16, default="PDF")
    notice = models.CharField(
        "تنويه",
        max_length=255,
        blank=True,
        default="",
        help_text="سطر توضيحي يظهر أسفل اسم المستند في صفحة المنتج.",
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "مستند منتج"
        verbose_name_plural = "مستندات المنتجات"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.label

    @property
    def src(self) -> str:
        if self.file:
            return self.file.url
        return self.legacy_path


class ProductRelation(models.Model):
    from_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="relations_from"
    )
    to_product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="relations_to"
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)

    class Meta:
        verbose_name = "منتج ذو صلة"
        verbose_name_plural = "المنتجات ذات الصلة"
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["from_product", "to_product"], name="unique_product_relation"
            ),
            models.CheckConstraint(
                condition=~models.Q(from_product=models.F("to_product")),
                name="product_relation_not_self",
            ),
        ]
