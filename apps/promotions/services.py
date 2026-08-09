"""Coupon eligibility and redemption (FR-080 – FR-086, INV-005)."""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.money import ZERO, percentage_of, quantize_money

from .models import Coupon, CouponRedemption, DiscountType

REJECTED_MESSAGE = "الكود غير صالح في العرض التجريبي."


class CouponError(ValidationError):
    pass


def find_coupon(code: str) -> Coupon | None:
    """Codes are case-insensitive on input, stored uppercase (FR-085)."""
    if not code:
        return None
    return Coupon.objects.filter(code=code.strip().upper()).first()


def validate_coupon(coupon: Coupon, subtotal: Decimal, *, customer=None, cart=None) -> None:
    """Raise if the coupon cannot be applied. Fails closed (FR-086)."""
    now = timezone.now()

    if not coupon.is_active:
        raise CouponError(REJECTED_MESSAGE)
    if coupon.starts_at and coupon.starts_at > now:
        raise CouponError(REJECTED_MESSAGE)
    # Expired and exhausted both answer with the *prototype's* rejection label
    # (FR-086). A distinct "this code has expired" / "this code is used up"
    # confirms to whoever typed it that the code is real — the same enumeration
    # oracle the coupon rate limiter exists to close (storefront/views.py, T-1707).
    if coupon.ends_at and coupon.ends_at <= now:
        raise CouponError(REJECTED_MESSAGE)
    if coupon.usage_limit is not None and coupon.times_used >= coupon.usage_limit:
        raise CouponError(REJECTED_MESSAGE)
    if coupon.minimum_subtotal is not None and subtotal < coupon.minimum_subtotal:
        raise CouponError(
            f"الحد الأدنى لاستخدام الكود هو {coupon.minimum_subtotal:.0f} ج.م."
        )
    if customer is not None and coupon.per_customer_limit is not None:
        used = CouponRedemption.objects.filter(coupon=coupon, customer=customer).count()
        if used >= coupon.per_customer_limit:
            raise CouponError("لقد استخدمت هذا الكود من قبل.")

    if cart is not None and (coupon.products.exists() or coupon.categories.exists()):
        product_ids = set(
            cart.lines.values_list("variant__product_id", flat=True)
        )
        category_ids = set(
            cart.lines.values_list("variant__product__category_id", flat=True)
        )
        allowed_products = set(coupon.products.values_list("id", flat=True))
        allowed_categories = set(coupon.categories.values_list("id", flat=True))
        if not (product_ids & allowed_products) and not (category_ids & allowed_categories):
            raise CouponError("لا ينطبق هذا الكود على محتويات سلتك.")


def compute_discount(coupon: Coupon, subtotal: Decimal, *, cart=None) -> Decimal:
    """Discount amount, capped and never exceeding the subtotal."""
    if subtotal <= ZERO:
        return ZERO
    if coupon.discount_type == DiscountType.PERCENTAGE:
        amount = percentage_of(subtotal, coupon.value)
        if coupon.max_discount is not None:
            amount = min(amount, quantize_money(coupon.max_discount))
    else:
        amount = quantize_money(coupon.value)
    return min(amount, quantize_money(subtotal))


@transaction.atomic
def redeem(coupon: Coupon, order, amount: Decimal, *, customer=None) -> CouponRedemption:
    """Consume one use, under a row lock (FR-083, INV-005).

    Called from inside the order transaction so a failure anywhere rolls the
    redemption back with everything else.
    """
    locked = Coupon.objects.select_for_update().get(pk=coupon.pk)
    if locked.usage_limit is not None and locked.times_used >= locked.usage_limit:
        raise CouponError(REJECTED_MESSAGE)  # exhausted fails closed (FR-086)

    locked.times_used += 1
    locked.save(update_fields=["times_used", "updated_at"])

    return CouponRedemption.objects.create(
        coupon=locked, order=order, customer=customer, amount=quantize_money(amount)
    )


@transaction.atomic
def reverse_redemption(order) -> int:
    """Give the use back when an order is cancelled."""
    reversed_count = 0
    for redemption in CouponRedemption.objects.select_related("coupon").filter(order=order):
        coupon = Coupon.objects.select_for_update().get(pk=redemption.coupon_id)
        coupon.times_used = max(0, coupon.times_used - 1)
        coupon.save(update_fields=["times_used", "updated_at"])
        redemption.delete()
        reversed_count += 1
    return reversed_count
