"""Cart and wishlist (FR-030 – FR-039).

The important correction to the prototype is the **line identity**. The approved
storefront adds a line keyed by ``(productId, finishId)`` but updates and removes
by ``productId`` alone::

    // static/src/js/state/store.js:24-26  add  -> keyed by product + finish
    // static/src/js/state/store.js:34,41  update/remove -> keyed by product ONLY

so two finishes of the same product cannot be managed independently. Here the
key is ``(cart, variant)`` for every operation, enforced by a database
constraint (FR-030).

No price is ever stored on a line: totals are recomputed from the variant on
every read, so the browser can never influence money (FR-034).
"""

from __future__ import annotations

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel

MAX_LINE_QUANTITY = 9  # matches the storefront bound at store.js:27-28


class CartStatus(models.TextChoices):
    ACTIVE = "active", "نشطة"
    MERGED = "merged", "مدموجة"
    CONVERTED = "converted", "محوّلة إلى طلب"
    ABANDONED = "abandoned", "متروكة"


class Cart(TimeStampedModel):
    customer = models.ForeignKey(
        "accounts.CustomerProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name="العميل",
    )
    session_key = models.CharField(
        "مفتاح الجلسة", max_length=64, blank=True, default="", db_index=True
    )
    status = models.CharField(
        "الحالة", max_length=16, choices=CartStatus.choices, default=CartStatus.ACTIVE
    )
    coupon = models.ForeignKey(
        "promotions.Coupon",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name="كود الخصم",
    )
    expires_at = models.DateTimeField("تنتهي في", null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "سلة"
        verbose_name_plural = "السلال"
        ordering = ["-updated_at"]
        constraints = [
            # One active cart per customer and per anonymous session.
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(status="active") & models.Q(customer__isnull=False),
                name="unique_active_cart_per_customer",
            ),
            models.UniqueConstraint(
                fields=["session_key"],
                condition=models.Q(status="active") & ~models.Q(session_key=""),
                name="unique_active_cart_per_session",
            ),
        ]

    def __str__(self) -> str:
        owner = self.customer or self.session_key or "مجهول"
        return f"سلة {owner}"

    @property
    def is_empty(self) -> bool:
        return not self.lines.exists()


class CartLine(TimeStampedModel):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="lines", verbose_name="السلة"
    )
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.PROTECT,
        related_name="cart_lines",
        verbose_name="الخيار",
    )
    quantity = models.PositiveSmallIntegerField(
        "الكمية",
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(MAX_LINE_QUANTITY)],
    )

    class Meta:
        verbose_name = "سطر سلة"
        verbose_name_plural = "أسطر السلة"
        ordering = ["created_at", "id"]
        constraints = [
            # FR-030: the canonical identity for add, update AND remove.
            models.UniqueConstraint(
                fields=["cart", "variant"], name="unique_variant_per_cart"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1)
                & models.Q(quantity__lte=MAX_LINE_QUANTITY),
                name="cart_line_quantity_within_bounds",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.variant.sku} × {self.quantity}"


class Wishlist(TimeStampedModel):
    customer = models.OneToOneField(
        "accounts.CustomerProfile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="wishlist",
        verbose_name="العميل",
    )
    session_key = models.CharField(
        "مفتاح الجلسة", max_length=64, blank=True, default="", db_index=True
    )

    class Meta:
        verbose_name = "قائمة مفضلة"
        verbose_name_plural = "قوائم المفضلة"

    def __str__(self) -> str:
        return f"مفضلة {self.customer or self.session_key or 'مجهول'}"


class WishlistItem(TimeStampedModel):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items", verbose_name="القائمة"
    )
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name="المنتج",
    )

    class Meta:
        verbose_name = "منتج مفضل"
        verbose_name_plural = "المنتجات المفضلة"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["wishlist", "product"], name="unique_product_per_wishlist"
            )
        ]

    def __str__(self) -> str:
        return self.product.name
