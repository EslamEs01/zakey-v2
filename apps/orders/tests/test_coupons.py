"""Coupons at order creation: re-evaluation, redemption, no stacking (T-0902 – T-0904).

The apply-time rules themselves are asserted one at a time in
``apps/core/tests/test_coupon_rules.py``. What is asserted here is what the
*order transaction* does with a coupon that a basket already carries: it makes
its own decision rather than trusting the earlier one, it records the use, and
it records exactly one.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.cart.models import Cart, CartLine
from apps.cart.services import price_cart
from apps.orders.models import Order, OrderEvent
from apps.orders.services import create_order
from apps.promotions.models import Coupon, CouponRedemption, DiscountType
from apps.promotions.services import redeem, validate_coupon

pytestmark = pytest.mark.django_db

ADDRESS = {
    "full_name": "ندى إبراهيم",
    "phone": "01012345678",
    "governorate_key": "cairo",
    "governorate_name": "القاهرة",
    "area_key": "cairo-nasr-city",
    "area_name": "مدينة نصر",
    "city": "مدينة نصر",
    "street": "شارع تجريبي 12",
    "building": "5",
}

#: 10% of the 7,490.00 EGP default variant.
EXPECTED_DISCOUNT = Decimal("749.00")


def _coupon(code="TENOFF", **overrides) -> Coupon:
    fields = {
        "code": code,
        "discount_type": DiscountType.PERCENTAGE,
        "value": Decimal("10"),
    }
    fields.update(overrides)
    return Coupon.objects.create(**fields)


def _cart(customer, variant, coupon=None) -> Cart:
    cart = Cart.objects.create(customer=customer, coupon=coupon)
    CartLine.objects.create(cart=cart, variant=variant, quantity=1)
    return cart


def _checkout(cart, *, key="idem-coupon", customer=None) -> Order:
    return create_order(
        cart=cart,
        email="nada@example.com",
        phone="01012345678",
        address_data=dict(ADDRESS),
        idempotency_key=key,
        customer=customer,
        terms_accepted=True,
    )


def _bare_order(customer=None, number="ZK-BARE-1") -> Order:
    return Order.objects.create(
        number=number,
        customer=customer,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=f"bare-{number}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


# ---------------------------------------------------------------------------
# T-0902 — the verdict is the server's, twice
# ---------------------------------------------------------------------------


def test_the_apply_endpoint_decides_eligibility_on_the_server(storefront):
    """FR-082 (apply time): the browser posts a code, never a verdict or an amount.

    The coupon here is real and active but its minimum basket is far out of
    reach, so a request that *asks* for the discount — and helpfully supplies
    one — still leaves the basket at full price.
    """
    from apps.catalog.models import ProductVariant

    variant = ProductVariant.objects.filter(
        product__slug="zakey-apex-pro", is_active=True
    ).first()
    _coupon(code="RICHONLY", value=Decimal("50"), minimum_subtotal=Decimal("999999.00"))

    storefront.post(
        reverse("storefront:cart-add"), {"variant": variant.pk, "quantity": 1}, follow=True
    )
    storefront.post(
        reverse("storefront:cart-coupon"),
        {"coupon": "richonly", "discount_total": "5000.00", "grand_total": "1.00"},
        follow=True,
    )

    cart = Cart.objects.get()
    assert cart.coupon is None, "an ineligible coupon was attached to the basket"

    totals = storefront.get(reverse("storefront:cart")).context["cart_totals"]
    assert totals.discount_total == Decimal("0.00")
    assert totals.grand_total == totals.subtotal


def test_a_coupon_accepted_at_apply_time_is_re_evaluated_at_order_creation(
    variant, stock, customer
):
    """FR-082: server-side at apply time, and evaluated again when the order is created.

    The validity window closes between the two — the one case a cached
    apply-time verdict gets wrong — and the order must be refused rather than
    honouring a decision that has since expired.
    """
    coupon = _coupon(ends_at=timezone.now() + timedelta(hours=1))
    cart = _cart(customer, variant)

    # Apply time: the server evaluates the coupon against the real basket and
    # computes the amount itself.
    validate_coupon(coupon, price_cart(cart).subtotal, customer=customer, cart=cart)
    cart.coupon = coupon
    cart.save(update_fields=["coupon", "updated_at"])
    assert price_cart(cart, coupon=coupon).discount_total == EXPECTED_DISCOUNT

    # …and then it expires while the customer is filling in their address.
    Coupon.objects.filter(pk=coupon.pk).update(
        ends_at=timezone.now() - timedelta(seconds=1)
    )

    # Checkout is a fresh request, so it reads the basket back from the database
    # exactly as ``storefront.views.checkout`` does.
    submitted = Cart.objects.get(pk=cart.pk)
    with pytest.raises(ValidationError):
        _checkout(submitted, customer=customer)

    assert not Order.objects.exists(), "an expired coupon still produced an order"
    assert not CouponRedemption.objects.exists()
    coupon.refresh_from_db()
    assert coupon.times_used == 0


def test_a_coupon_still_valid_at_submission_is_honoured(variant, stock, customer):
    coupon = _coupon(ends_at=timezone.now() + timedelta(hours=1))
    order = _checkout(_cart(customer, variant, coupon=coupon), customer=customer)

    assert order.coupon_code == "TENOFF"
    assert order.discount_total == EXPECTED_DISCOUNT
    assert order.grand_total == order.subtotal - EXPECTED_DISCOUNT


# ---------------------------------------------------------------------------
# T-0903 — the use is recorded, transactionally, under a lock
# ---------------------------------------------------------------------------


class TestRedemptionIsRecorded:
    """FR-083: usage recorded per order and per customer, incremented inside the
    order transaction under a row lock.

    Each of those four words gets its own test: the row exists and names both
    the order and the customer; a failure later in ``create_order`` takes the
    increment down with it; and the increment is issued behind
    ``SELECT … FOR UPDATE`` on the coupon row rather than a bare read.
    """

    def test_a_redemption_row_names_the_order_and_the_customer(
        self, variant, stock, customer
    ):
        coupon = _coupon()
        order = _checkout(_cart(customer, variant, coupon=coupon), customer=customer)

        redemption = CouponRedemption.objects.get()
        assert redemption.order_id == order.pk
        assert redemption.customer_id == customer.pk
        assert redemption.coupon_id == coupon.pk
        assert redemption.amount == EXPECTED_DISCOUNT

        coupon.refresh_from_db()
        assert coupon.times_used == 1

    def test_a_guest_checkout_still_records_the_use_against_the_order(
        self, variant, stock
    ):
        coupon = _coupon()
        order = _checkout(_cart(None, variant, coupon=coupon))

        redemption = CouponRedemption.objects.get()
        assert redemption.order_id == order.pk
        assert redemption.customer_id is None
        coupon.refresh_from_db()
        assert coupon.times_used == 1

    def test_a_failure_after_the_redemption_rolls_the_usage_back(
        self, monkeypatch, variant, stock, customer
    ):
        """The increment is inside the order transaction, not beside it."""
        coupon = _coupon()
        cart = _cart(customer, variant, coupon=coupon)

        def boom(*args, **kwargs):
            raise RuntimeError("order transaction failed after the coupon was consumed")

        # The order event is written after step 6 (the redemption), so this
        # fails the transaction at a point where the use has already been taken.
        monkeypatch.setattr(OrderEvent.objects, "create", boom)

        with pytest.raises(RuntimeError):
            _checkout(cart, customer=customer)

        assert not Order.objects.exists()
        assert not CouponRedemption.objects.exists()
        coupon.refresh_from_db()
        assert coupon.times_used == 0, "a use survived a rolled-back order"

    def test_the_count_is_raised_behind_a_row_lock_on_the_coupon(self, customer):
        coupon = _coupon()
        order = _bare_order(customer)

        with CaptureQueriesContext(connection) as captured:
            redeem(coupon, order, Decimal("749.00"), customer=customer)

        table = Coupon._meta.db_table
        locked_reads = [
            query["sql"]
            for query in captured.captured_queries
            if table in query["sql"] and "FOR UPDATE" in query["sql"].upper()
        ]
        assert locked_reads, (
            "the coupon row was read without SELECT ... FOR UPDATE; two "
            "concurrent orders could both see the same times_used"
        )

    def test_the_last_use_of_an_exhausted_coupon_cannot_be_taken_twice(self, customer):
        coupon = _coupon(usage_limit=1)
        redeem(coupon, _bare_order(customer, "ZK-BARE-A"), Decimal("100.00"))

        from apps.promotions.services import CouponError

        with pytest.raises(CouponError):
            redeem(coupon, _bare_order(customer, "ZK-BARE-B"), Decimal("100.00"))

        coupon.refresh_from_db()
        assert coupon.times_used == 1


# ---------------------------------------------------------------------------
# T-0904 — one coupon per order
# ---------------------------------------------------------------------------


class TestOneCouponPerOrder:
    """FR-084: coupons do not stack.

    A basket can name one code — the field is a foreign key, not a collection —
    a second code replaces the first rather than joining it, and the order that
    results carries exactly one code and one redemption row.
    """

    def test_a_basket_names_one_coupon_not_a_collection(self):
        field = Cart._meta.get_field("coupon")
        assert field.many_to_one, "Cart.coupon is not a single-valued relation"
        assert not field.many_to_many, "a basket can hold more than one coupon"

    def test_applying_a_second_coupon_replaces_the_first(self, variant, stock, customer):
        first = _coupon(code="FIRST")
        second = _coupon(code="SECOND", value=Decimal("20"))
        cart = _cart(customer, variant, coupon=first)

        cart.coupon = second
        cart.save(update_fields=["coupon", "updated_at"])
        cart.refresh_from_db()

        assert cart.coupon_id == second.pk
        # The discount is the second coupon's alone; the two do not sum.
        assert price_cart(cart, coupon=cart.coupon).discount_total == Decimal("1498.00")

    def test_an_order_carries_one_code_and_one_redemption(
        self, variant, stock, customer
    ):
        coupon = _coupon()
        order = _checkout(_cart(customer, variant, coupon=coupon), customer=customer)

        assert order.coupon_code == "TENOFF"
        assert order.coupon_redemptions.count() == 1
        assert CouponRedemption.objects.filter(order=order).count() == 1

    def test_the_database_refuses_a_second_redemption_of_one_coupon_on_one_order(
        self, variant, stock, customer
    ):
        coupon = _coupon()
        order = _checkout(_cart(customer, variant, coupon=coupon), customer=customer)

        with pytest.raises(IntegrityError), transaction.atomic():
            CouponRedemption.objects.create(
                coupon=coupon, order=order, customer=customer, amount=Decimal("1.00")
            )
