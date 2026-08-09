"""Order creation as a single transaction, and the order number (FR-061, FR-065).

``create_order`` writes six things — the order, its lines, its address, the
stock reservation, the coupon consumption and the creation event. Either all
six exist or none of them do; a half-written order is worse than no order,
because it holds stock and burns a coupon for a purchase that never happened.

The failure tests here do not merely *arrange* for a failure before anything is
written. They let the work happen and then blow up at the last step, so the
assertions afterwards are about a rollback that had something real to undo.

No commercial figure appears anywhere below: no shipping rate and no
installation fee are quoted, because both are still unapproved business input
(T-2006). The only money involved is the catalogue price already under test
elsewhere and a plainly fake demonstration coupon.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.cart.models import CartStatus
from apps.cart.services import add_to_cart, get_or_create_cart
from apps.inventory import services as inventory_services
from apps.inventory.models import StockReservation
from apps.inventory.services import InsufficientStock
from apps.orders.models import Order, OrderAddress, OrderEvent, OrderLine
from apps.orders.services import create_order, generate_order_number
from apps.promotions.models import Coupon, CouponRedemption, DiscountType

pytestmark = pytest.mark.django_db

ADDRESS = {
    "full_name": "ندى إبراهيم",
    "phone": "01012345678",
    "governorate_key": "cairo",
    "governorate_name": "القاهرة",
    "area_key": "",
    "area_name": "",
    "city": "القاهرة",
    "street": "١٢ شارع التحرير",
    "building": "٥",
    "landmark": "",
}


def make_cart(session_key: str, *lines, coupon=None):
    """A cart holding ``(variant, quantity)`` pairs, optionally couponed."""
    cart = get_or_create_cart(session_key=session_key)
    for variant, quantity in lines:
        add_to_cart(cart, variant, quantity)
    if coupon is not None:
        cart.coupon = coupon
        cart.save(update_fields=["coupon", "updated_at"])
    return cart


def place(cart, *, key: str = "t1806-order-key", **kwargs):
    kwargs.setdefault("terms_accepted", True)
    return create_order(
        cart=cart,
        email="nada@example.com",
        phone="01012345678",
        address_data=dict(ADDRESS),
        idempotency_key=key,
        **kwargs,
    )


def tenth_off(code: str = "FR061TENTH") -> Coupon:
    return Coupon.objects.create(
        code=code,
        discount_type=DiscountType.PERCENTAGE,
        value=Decimal("10.00"),
        is_demo=True,
    )


class TestOrderCreationIsOneTransaction:
    def test_one_call_writes_every_part_of_the_order(self, variant, stock, site_setting):
        """FR-061: the transaction covers all five kinds of write at once.

        This is the positive control for the rollback tests below: it pins down
        exactly what a successful creation leaves behind, so "nothing survives"
        afterwards means something.
        """
        coupon = tenth_off()
        cart = make_cart("fr061-ok", (variant, 2), coupon=coupon)

        order = place(cart, key="fr061-ok")

        assert Order.objects.count() == 1
        assert order.lines.count() == 1  # order write + line snapshot
        assert OrderAddress.objects.filter(order=order).exists()
        assert StockReservation.objects.filter(order=order).count() == 1  # reservation
        assert CouponRedemption.objects.filter(order=order).count() == 1  # consumption
        assert order.events.filter(event_type="created").count() == 1  # event write

        stock.refresh_from_db()
        assert stock.reserved == 2
        coupon.refresh_from_db()
        assert coupon.times_used == 1
        cart.refresh_from_db()
        assert cart.status == CartStatus.CONVERTED

    def test_a_failure_consuming_the_coupon_undoes_everything_before_it(
        self, monkeypatch, variant, stock, site_setting
    ):
        """FR-061: the order, the line, the address, the reservation and the
        coupon use all disappear when the last step fails.

        The stand-in for ``redeem`` deliberately *succeeds* first — it takes the
        coupon use and writes the redemption row — and only then raises. So the
        rollback is not merely skipping work that never ran; it has to reverse
        writes that really happened inside the transaction.
        """
        coupon = tenth_off("FR061BOOM")
        cart = make_cart("fr061-boom", (variant, 1), coupon=coupon)

        def exploding_redeem(coupon_, order_, amount, *, customer=None):
            locked = Coupon.objects.select_for_update().get(pk=coupon_.pk)
            locked.times_used += 1
            locked.save(update_fields=["times_used", "updated_at"])
            CouponRedemption.objects.create(
                coupon=locked, order=order_, customer=customer, amount=amount
            )
            raise ValidationError("فشل مُصطنع بعد استهلاك الكود.")

        monkeypatch.setattr("apps.promotions.services.redeem", exploding_redeem)

        with pytest.raises(ValidationError):
            place(cart, key="fr061-boom")

        assert Order.objects.count() == 0
        assert OrderLine.objects.count() == 0
        assert OrderAddress.objects.count() == 0
        assert OrderEvent.objects.count() == 0
        assert StockReservation.objects.count() == 0
        assert CouponRedemption.objects.count() == 0

        stock.refresh_from_db()
        assert stock.reserved == 0, "a rolled-back order must not hold stock"
        coupon.refresh_from_db()
        assert coupon.times_used == 0, "a rolled-back order must not burn a coupon use"

        # …and the customer still has their basket.
        cart.refresh_from_db()
        assert cart.status == CartStatus.ACTIVE
        assert cart.lines.count() == 1

    def test_a_failure_reserving_the_second_line_releases_the_first(
        self, monkeypatch, variant, stock, second_variant, second_stock, site_setting
    ):
        """FR-061: stock running out mid-flight leaves no partial reservation.

        The first line reserves successfully and the second finds nothing left.
        Without a single transaction the first reservation would survive and
        quietly hold stock for an order that was never created.
        """
        cart = make_cart("fr061-stock", (variant, 2), (second_variant, 3))
        real_reserve = inventory_services.reserve
        calls = {"n": 0}

        def flaky_reserve(target_variant, quantity, **kwargs):
            calls["n"] += 1
            if calls["n"] == 2:
                raise InsufficientStock(target_variant, quantity, 0)
            return real_reserve(target_variant, quantity, **kwargs)

        monkeypatch.setattr(inventory_services, "reserve", flaky_reserve)

        with pytest.raises(InsufficientStock):
            place(cart, key="fr061-stock")

        assert calls["n"] == 2, "the first line must really have been reserved"
        assert Order.objects.count() == 0
        assert OrderLine.objects.count() == 0
        assert StockReservation.objects.count() == 0

        stock.refresh_from_db()
        second_stock.refresh_from_db()
        assert stock.reserved == 0
        assert second_stock.reserved == 0

    def test_an_unacceptable_submission_writes_nothing_at_all(
        self, variant, stock, site_setting
    ):
        """FR-061: validation is inside the same transaction as the writes.

        Refusing after the order row exists would be indistinguishable, from the
        database's point of view, from accepting it.
        """
        cart = make_cart("fr061-terms", (variant, 1))

        with pytest.raises(ValidationError):
            place(cart, key="fr061-terms", terms_accepted=False)

        assert Order.objects.count() == 0
        assert OrderEvent.objects.count() == 0
        assert StockReservation.objects.count() == 0
        stock.refresh_from_db()
        assert stock.reserved == 0


class TestOrderNumber:
    def test_numbers_are_readable_unique_and_not_a_running_counter(self, site_setting):
        """FR-065: readable shape, no repeats, and no arithmetic to follow.

        Sixty numbers are generated in a row. A sequential scheme would show up
        immediately as an ascending run with steps of one — which is exactly the
        pattern that lets a customer who orders twice measure how much the shop
        sold in between.
        """
        prefix = site_setting.order_number_prefix
        numbers = [generate_order_number() for _ in range(60)]

        assert len(set(numbers)) == 60, "generated numbers must be unique"

        shape = re.compile(rf"^{re.escape(prefix)}-\d{{6}}-[0-9A-F]{{6}}$")
        for number in numbers:
            assert shape.match(number), f"unreadable order number: {number!r}"
            assert number.isascii(), "an order number is read aloud over the phone"
            assert len(number) <= 32  # the column's width

        suffixes = [int(number.rsplit("-", 1)[1], 16) for number in numbers]
        assert all(
            abs(later - earlier) != 1 for earlier, later in zip(suffixes, suffixes[1:])
        ), "consecutive order numbers must not differ by one"
        assert suffixes != sorted(suffixes), "order numbers must not ascend like a counter"

    def test_two_orders_placed_back_to_back_are_not_neighbours(
        self, variant, stock, second_variant, second_stock, site_setting
    ):
        """FR-065: the property holds for real orders, not just the generator."""
        first = place(make_cart("fr065-a", (variant, 1)), key="fr065-a")
        second = place(make_cart("fr065-b", (second_variant, 1)), key="fr065-b")

        assert first.number != second.number
        earlier = int(first.number.rsplit("-", 1)[1], 16)
        later = int(second.number.rsplit("-", 1)[1], 16)
        assert abs(later - earlier) != 1

    def test_the_database_refuses_a_second_order_with_the_same_number(self, site_setting):
        """FR-065: uniqueness is a constraint, which is what makes it survive
        concurrency — two racing writers cannot both win."""
        Order.objects.create(
            number="ZK-000000-ABCDEF",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="fr065-unique-1",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            Order.objects.create(
                number="ZK-000000-ABCDEF",
                email="nada@example.com",
                phone="01012345678",
                idempotency_key="fr065-unique-2",
                subtotal=Decimal("100.00"),
                grand_total=Decimal("100.00"),
            )
