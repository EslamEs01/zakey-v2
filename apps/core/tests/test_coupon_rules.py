"""Coupon discount shape, eligibility rules, code casing and refusal (T-0901 – T-0904).

These exercise ``apps.promotions`` directly, without an HTTP request, so every
rule can be failed on its own. The order-creation side of coupons — re-evaluation,
redemption recording and the no-stacking rule — lives in
``apps/orders/tests/test_coupons.py``.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.cart.models import Cart, CartLine
from apps.orders.models import Order
from apps.promotions.models import Coupon, CouponRedemption, DiscountType
from apps.promotions.services import (
    REJECTED_MESSAGE,
    CouponError,
    compute_discount,
    find_coupon,
    validate_coupon,
)

pytestmark = pytest.mark.django_db

SUBTOTAL = Decimal("7490.00")


def _coupon(**overrides) -> Coupon:
    fields = {
        "code": "ZAKEYTEST",
        "discount_type": DiscountType.PERCENTAGE,
        "value": Decimal("10.00"),
    }
    fields.update(overrides)
    return Coupon.objects.create(**fields)


def _cart_with(variant, customer=None) -> Cart:
    cart = Cart.objects.create(customer=customer)
    CartLine.objects.create(cart=cart, variant=variant, quantity=1)
    return cart


def _order(customer=None, number="ZK-COUPON-1") -> Order:
    return Order.objects.create(
        number=number,
        customer=customer,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=f"idem-{number}",
        subtotal=SUBTOTAL,
        grand_total=SUBTOTAL,
    )


# ---------------------------------------------------------------------------
# T-0901 — the two discount shapes and the cap
# ---------------------------------------------------------------------------


class TestDiscountShape:
    def test_a_fixed_coupon_discounts_its_exact_value(self):
        """FR-080: fixed discounts are supported and are not a percentage."""
        coupon = _coupon(discount_type=DiscountType.FIXED, value=Decimal("250.00"))
        assert compute_discount(coupon, SUBTOTAL) == Decimal("250.00")

    def test_a_percentage_coupon_discounts_a_share_of_the_subtotal(self):
        """FR-080: percentage discounts are supported."""
        coupon = _coupon(discount_type=DiscountType.PERCENTAGE, value=Decimal("10"))
        # 10% of 7,490 — not a flat 10.
        assert compute_discount(coupon, SUBTOTAL) == Decimal("749.00")

    def test_the_maximum_discount_caps_a_percentage(self):
        """FR-080: the cap binds a percentage discount that would exceed it."""
        coupon = _coupon(
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal("50"),
            max_discount=Decimal("500.00"),
        )
        # Uncapped this is 3,745.00; the cap is what the customer gets.
        assert compute_discount(coupon, SUBTOTAL) == Decimal("500.00")

    def test_the_cap_never_inflates_a_smaller_discount(self):
        coupon = _coupon(
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal("5"),
            max_discount=Decimal("5000.00"),
        )
        assert compute_discount(coupon, SUBTOTAL) == Decimal("374.50")

    def test_a_discount_never_exceeds_the_subtotal(self):
        """A 10,000 EGP coupon on a 7,490 EGP basket must not create change."""
        coupon = _coupon(discount_type=DiscountType.FIXED, value=Decimal("10000.00"))
        assert compute_discount(coupon, SUBTOTAL) == SUBTOTAL

    def test_a_percentage_above_one_hundred_is_refused_by_validation(self):
        from django.core.exceptions import ValidationError

        coupon = Coupon(
            code="TOOMUCH", discount_type=DiscountType.PERCENTAGE, value=Decimal("140")
        )
        with pytest.raises(ValidationError):
            coupon.clean()


# ---------------------------------------------------------------------------
# T-0902 — every eligibility rule, failed one at a time
# ---------------------------------------------------------------------------


class TestEligibilityRules:
    """FR-081: each clause the requirement names, refused on its own.

    Validity window, total usage limit, per-customer limit, minimum basket
    amount and product/category restriction each get a test that moves exactly
    one of them out of range and leaves the rest satisfiable, so a rule that
    stopped being checked fails here rather than hiding behind another.
    """

    def test_a_coupon_before_its_window_is_refused(self):
        coupon = _coupon(starts_at=timezone.now() + timedelta(hours=1))
        with pytest.raises(CouponError):
            validate_coupon(coupon, SUBTOTAL)

    def test_a_coupon_after_its_window_is_refused(self):
        coupon = _coupon(
            starts_at=timezone.now() - timedelta(days=2),
            ends_at=timezone.now() - timedelta(hours=1),
        )
        with pytest.raises(CouponError):
            validate_coupon(coupon, SUBTOTAL)

    def test_a_coupon_inside_its_window_is_accepted(self):
        coupon = _coupon(
            starts_at=timezone.now() - timedelta(hours=1),
            ends_at=timezone.now() + timedelta(hours=1),
        )
        validate_coupon(coupon, SUBTOTAL)  # must not raise

    def test_the_total_usage_limit_is_enforced(self):
        coupon = _coupon(usage_limit=2, times_used=1)
        validate_coupon(coupon, SUBTOTAL)  # one use left

        Coupon.objects.filter(pk=coupon.pk).update(times_used=2)
        coupon.refresh_from_db()
        with pytest.raises(CouponError):
            validate_coupon(coupon, SUBTOTAL)

    def test_the_per_customer_limit_is_enforced(self, customer, other_customer):
        coupon = _coupon(per_customer_limit=1)
        CouponRedemption.objects.create(
            coupon=coupon,
            order=_order(customer),
            customer=customer,
            amount=Decimal("100.00"),
        )

        with pytest.raises(CouponError):
            validate_coupon(coupon, SUBTOTAL, customer=customer)

        # The ceiling is per customer, so somebody else is still eligible.
        validate_coupon(coupon, SUBTOTAL, customer=other_customer)

    def test_the_minimum_basket_amount_is_enforced(self):
        coupon = _coupon(minimum_subtotal=Decimal("5000.00"))
        with pytest.raises(CouponError):
            validate_coupon(coupon, Decimal("4999.99"))
        validate_coupon(coupon, Decimal("5000.00"))  # exactly on the line qualifies

    def test_a_product_restricted_coupon_refuses_a_basket_without_that_product(
        self, variant, product, category
    ):
        from apps.catalog.models import Product, ProductVariant
        from apps.core.models import PublicationStatus

        other_product = Product.objects.create(
            slug="zakey-other-lock",
            name="قفل آخر",
            category=category,
            status=PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        other_variant = ProductVariant.objects.create(
            product=other_product,
            sku="ZK-OTHER-1",
            finish_label="فضي",
            price=Decimal("3990.00"),
            is_default=True,
        )

        coupon = _coupon()
        coupon.products.add(product)

        with pytest.raises(CouponError):
            validate_coupon(coupon, SUBTOTAL, cart=_cart_with(other_variant))
        validate_coupon(coupon, SUBTOTAL, cart=_cart_with(variant))

    def test_a_category_restricted_coupon_follows_the_category(
        self, variant, category, product
    ):
        from apps.catalog.models import Category

        empty_category = Category.objects.create(slug="doorbells", name="أجراس")

        coupon = _coupon()
        coupon.categories.add(empty_category)
        with pytest.raises(CouponError):
            validate_coupon(coupon, SUBTOTAL, cart=_cart_with(variant))

        coupon.categories.set([category])
        validate_coupon(coupon, SUBTOTAL, cart=_cart_with(variant))

    def test_an_unrestricted_coupon_applies_to_any_basket(self, variant):
        validate_coupon(_coupon(), SUBTOTAL, cart=_cart_with(variant))


# ---------------------------------------------------------------------------
# T-0902 — code casing, matching the browser
# ---------------------------------------------------------------------------


class TestCodeCasing:
    def test_a_code_is_stored_uppercase_however_it_was_typed(self):
        """FR-085: storage is uppercase, whatever casing or padding arrived."""
        coupon = _coupon(code="  zakeyDemo  ")
        coupon.refresh_from_db()
        assert coupon.code == "ZAKEYDEMO"

    @pytest.mark.parametrize(
        "typed", ["zakeydemo", "ZaKeYdEmO", "ZAKEYDEMO", "  zakeydemo  "]
    )
    def test_lookup_is_case_insensitive_on_input(self, typed):
        """FR-085: any casing the customer types finds the stored code."""
        coupon = _coupon(code="ZAKEYDEMO")
        assert find_coupon(typed) == coupon

    def test_the_server_repeats_the_uppercasing_the_browser_does(self):
        """FR-085: mirrors ``.toUpperCase()`` at ``cart.js:141``.

        The browser normalises before it posts; the server must not trust that
        it did, so ``CouponForm`` performs the same trim-and-uppercase.
        """
        from storefront.forms import CouponForm

        form = CouponForm({"coupon": "  zakeydemo  "})
        assert form.is_valid()
        assert form.cleaned_data["coupon"] == "ZAKEYDEMO"


# ---------------------------------------------------------------------------
# T-0904 — exhausted and expired fail closed
# ---------------------------------------------------------------------------


class TestExhaustedOrExpiredFailsClosed:
    """FR-086: both refusals use the rejection message the prototype already shows.

    "Fails closed" is two claims, and both are asserted here: the coupon is not
    applied *and* the customer is told nothing that distinguishes a real code
    from an invented one.
    """

    def test_an_expired_coupon_is_refused_with_the_existing_rejection_message(self):
        coupon = _coupon(ends_at=timezone.now() - timedelta(seconds=1))
        with pytest.raises(CouponError) as raised:
            validate_coupon(coupon, SUBTOTAL)
        assert raised.value.messages == ["الكود غير صالح في العرض التجريبي."]

    def test_an_exhausted_coupon_is_refused_with_the_existing_rejection_message(self):
        coupon = _coupon(usage_limit=3, times_used=3)
        with pytest.raises(CouponError) as raised:
            validate_coupon(coupon, SUBTOTAL)
        assert raised.value.messages == ["الكود غير صالح في العرض التجريبي."]

    # That this string is the prototype's own — `site.couponPrototype
    # .rejectedLabel` — is proved in tests/fixtures/test_coupon_message_identity.py.
    # Nothing under apps/ may name the approved dataset (T-1608; enforced by
    # tests/test_backend_boundary.py::DatasetBoundaryTests).

    def test_a_refused_coupon_neither_leaks_nor_discounts(self):
        """Nothing about the refusal says the code exists, and no money moves."""
        expired = _coupon(code="EXPIRED", ends_at=timezone.now() - timedelta(seconds=1))
        exhausted = _coupon(code="USEDUP", usage_limit=1, times_used=1)

        messages = set()
        for coupon in (expired, exhausted):
            before = coupon.times_used
            with pytest.raises(CouponError) as raised:
                validate_coupon(coupon, SUBTOTAL)
            messages.update(raised.value.messages)
            coupon.refresh_from_db()
            assert coupon.times_used == before, "a refusal consumed a use"

        # A prober cannot tell "expired", "used up" and "never existed" apart.
        assert messages == {REJECTED_MESSAGE}
        assert find_coupon("NEVER-EXISTED") is None
