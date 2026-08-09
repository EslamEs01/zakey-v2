"""Cart services and server-authoritative pricing (FR-030 – FR-039).

**The browser is never trusted for money.** Requests carry variant ids,
quantities and a coupon code — never a price, VAT, discount, shipping cost or
total. Everything monetary is recomputed here from database rows (FR-034).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.catalog.models import Availability, ProductVariant
from apps.core.models import SiteSetting
from apps.core.money import ZERO, extract_vat, line_total, quantize_money

from .models import Cart, CartLine, CartStatus, Wishlist, WishlistItem


@dataclass
class PricedLine:
    line: CartLine
    variant: ProductVariant
    unit_price: Decimal
    quantity: int
    total: Decimal
    available: bool
    reason: str = ""


@dataclass
class CartTotals:
    """Every figure the storefront renders, computed server-side."""

    lines: list[PricedLine] = field(default_factory=list)
    subtotal: Decimal = ZERO
    discount_total: Decimal = ZERO
    coupon_code: str = ""
    shipping_total: Decimal = ZERO
    shipping_label: str = ""
    installation_total: Decimal = ZERO
    installation_requested: bool = False
    vat_amount: Decimal = ZERO
    vat_rate: Decimal = Decimal("0.1400")
    grand_total: Decimal = ZERO
    free_shipping_qualified: bool = False
    remaining_for_free_shipping: Decimal = ZERO
    unavailable_lines: list[PricedLine] = field(default_factory=list)
    used_placeholder_rates: bool = False

    @property
    def has_unavailable(self) -> bool:
        return bool(self.unavailable_lines)


def get_or_create_cart(*, customer=None, session_key: str = "") -> Cart:
    if customer is None and not session_key:
        raise ValidationError("السلة تحتاج إلى عميل أو جلسة.")
    settings_obj = SiteSetting.objects.get_solo()
    expires = timezone.now() + timedelta(days=settings_obj.cart_ttl_days)
    lookup = {"customer": customer} if customer else {"session_key": session_key}
    cart, created = Cart.objects.get_or_create(
        status=CartStatus.ACTIVE, defaults={"expires_at": expires}, **lookup
    )
    if not created:
        cart.expires_at = expires
        cart.save(update_fields=["expires_at", "updated_at"])
    return cart


def _max_quantity() -> int:
    return SiteSetting.objects.get_solo().max_line_quantity


@transaction.atomic
def add_to_cart(cart: Cart, variant: ProductVariant, quantity: int = 1) -> CartLine:
    """Add or increase a line, keyed on (cart, variant) (FR-030)."""
    if quantity < 1:
        raise ValidationError("الكمية يجب أن تكون 1 على الأقل.")
    if not variant.is_active or not variant.product.is_published:
        raise ValidationError("هذا المنتج غير متاح للشراء حاليًا.")
    if variant.product.availability == Availability.UNAVAILABLE:
        raise ValidationError("هذا المنتج غير متاح حاليًا.")

    maximum = _max_quantity()
    line, created = CartLine.objects.select_for_update().get_or_create(
        cart=cart, variant=variant, defaults={"quantity": min(quantity, maximum)}
    )
    if not created:
        line.quantity = min(line.quantity + quantity, maximum)
        line.save(update_fields=["quantity", "updated_at"])

    stock = getattr(variant, "stock_item", None)
    if stock is not None and line.quantity > stock.available:
        line.quantity = max(1, stock.available)
        line.save(update_fields=["quantity", "updated_at"])
        if stock.available <= 0:
            line.delete()
            raise ValidationError("نفدت الكمية المتاحة من هذا المنتج.")
    return line


@transaction.atomic
def update_quantity(cart: Cart, variant: ProductVariant, quantity: int) -> CartLine | None:
    """Update ONE line, identified by (cart, variant) - not by product (FR-030)."""
    line = CartLine.objects.select_for_update().filter(cart=cart, variant=variant).first()
    if line is None:
        raise ValidationError("هذا المنتج غير موجود في السلة.")
    if quantity <= 0:
        line.delete()
        return None
    line.quantity = max(1, min(quantity, _max_quantity()))
    line.save(update_fields=["quantity", "updated_at"])
    return line


@transaction.atomic
def remove_from_cart(cart: Cart, variant: ProductVariant) -> None:
    """Remove ONE line, identified by (cart, variant) (FR-030)."""
    CartLine.objects.filter(cart=cart, variant=variant).delete()


def price_cart(
    cart: Cart,
    *,
    coupon=None,
    shipping_quote=None,
    installation_quote=None,
) -> CartTotals:
    """Recompute every monetary figure from the database (FR-034, FR-040).

    ``shipping_quote`` / ``installation_quote`` are optional
    ``(amount, label, is_placeholder)`` tuples supplied by the shipping service
    once an address is known.
    """
    settings_obj = SiteSetting.objects.get_solo()
    totals = CartTotals(vat_rate=settings_obj.vat_rate)

    lines = cart.lines.select_related(
        "variant__product", "variant__stock_item"
    ).order_by("created_at", "id")

    subtotal = ZERO
    for line in lines:
        variant = line.variant
        stock = getattr(variant, "stock_item", None)
        purchasable = (
            variant.is_active
            and variant.product.is_published
            and stock is not None
            and stock.available >= line.quantity
        )
        priced = PricedLine(
            line=line,
            variant=variant,
            unit_price=variant.price,
            quantity=line.quantity,
            total=line_total(variant.price, line.quantity),
            available=purchasable,
            reason="" if purchasable else "غير متاح بالكمية المطلوبة",
        )
        totals.lines.append(priced)
        if purchasable:
            subtotal += priced.total
        else:
            # Flagged and excluded from totals, never silently dropped (FR-035).
            totals.unavailable_lines.append(priced)

    totals.subtotal = quantize_money(subtotal)

    if coupon is not None:
        from apps.promotions.services import compute_discount

        totals.discount_total = compute_discount(coupon, totals.subtotal, cart=cart)
        totals.coupon_code = coupon.code

    discounted = quantize_money(totals.subtotal - totals.discount_total)

    # Free shipping is evaluated on the DISCOUNTED subtotal (FR-046).
    threshold = settings_obj.free_shipping_threshold
    totals.free_shipping_qualified = discounted >= threshold
    totals.remaining_for_free_shipping = max(ZERO, quantize_money(threshold - discounted))

    if shipping_quote is not None:
        amount, label, placeholder = shipping_quote
        totals.shipping_total = quantize_money(amount)
        totals.shipping_label = label
        totals.used_placeholder_rates = totals.used_placeholder_rates or placeholder

    if installation_quote is not None:
        amount, placeholder = installation_quote
        totals.installation_total = quantize_money(amount)
        totals.installation_requested = totals.installation_total > ZERO or placeholder is not None
        totals.used_placeholder_rates = totals.used_placeholder_rates or bool(placeholder)

    totals.grand_total = quantize_money(
        discounted + totals.shipping_total + totals.installation_total
    )
    # VAT is EXTRACTED from the gross total, never added to it (INV-011).
    totals.vat_amount = extract_vat(totals.grand_total, settings_obj.vat_rate)
    return totals


@transaction.atomic
def merge_carts(anonymous: Cart, target: Cart) -> Cart:
    """Merge an anonymous cart into the account cart on sign-in (FR-032).

    Quantities are summed then clamped to available stock and the per-line
    maximum, so a merge can never create an unfulfillable cart.
    """
    if anonymous.pk == target.pk:
        return target

    maximum = _max_quantity()
    for line in anonymous.lines.select_related("variant__stock_item"):
        existing = CartLine.objects.filter(cart=target, variant=line.variant).first()
        stock = getattr(line.variant, "stock_item", None)
        available = stock.available if stock else 0
        if existing:
            merged = existing.quantity + line.quantity
        else:
            merged = line.quantity
        clamped = max(1, min(merged, maximum, available if available > 0 else merged))
        if available <= 0:
            continue
        if existing:
            existing.quantity = clamped
            existing.save(update_fields=["quantity", "updated_at"])
        else:
            CartLine.objects.create(cart=target, variant=line.variant, quantity=clamped)

    if target.coupon is None and anonymous.coupon is not None:
        target.coupon = anonymous.coupon
        target.save(update_fields=["coupon", "updated_at"])

    anonymous.status = CartStatus.MERGED
    anonymous.save(update_fields=["status", "updated_at"])
    return target


# --- wishlist ---------------------------------------------------------------


def get_or_create_wishlist(*, customer=None, session_key: str = "") -> Wishlist:
    if customer is None and not session_key:
        raise ValidationError("قائمة المفضلة تحتاج إلى عميل أو جلسة.")
    lookup = {"customer": customer} if customer else {"session_key": session_key}
    wishlist, _ = Wishlist.objects.get_or_create(**lookup)
    return wishlist


@transaction.atomic
def toggle_wishlist(wishlist: Wishlist, product) -> bool:
    """Return True when the product ends up saved."""
    item = WishlistItem.objects.filter(wishlist=wishlist, product=product).first()
    if item:
        item.delete()
        return False
    WishlistItem.objects.create(wishlist=wishlist, product=product)
    return True


@transaction.atomic
def merge_wishlists(anonymous: Wishlist, target: Wishlist) -> Wishlist:
    for item in anonymous.items.all():
        WishlistItem.objects.get_or_create(wishlist=target, product=item.product)
    anonymous.items.all().delete()
    return target


def expire_carts(now=None) -> int:
    """Idempotent cleanup (FR-038)."""
    now = now or timezone.now()
    return Cart.objects.filter(
        status=CartStatus.ACTIVE, expires_at__lt=now
    ).update(status=CartStatus.ABANDONED, updated_at=now)
