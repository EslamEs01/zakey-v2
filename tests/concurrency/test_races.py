"""PostgreSQL concurrency evidence (NFR-005, SC-002, SC-003, SC-004).

These use real threads and real transactions. ``TransactionTestCase`` is
required because the default ``TestCase`` wraps each test in one transaction,
which would hide every locking interaction and make the suite a false negative.

SQLite cannot run these at all: it ignores ``SELECT ... FOR UPDATE``. conftest
refuses a non-PostgreSQL backend outright.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from unittest import mock

from django.db import connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone

from apps.accounts.models import CustomerProfile, User
from apps.cart.models import Cart, CartLine
from apps.cart.services import add_to_cart
from apps.catalog.models import Category, Product, ProductVariant
from apps.core.models import PublicationStatus, SiteSetting
from apps.inventory.models import StockItem, StockMovement, StockReservation
from apps.orders.models import Order
from apps.orders.services import create_order
from apps.promotions.models import Coupon, DiscountType
from apps.promotions.services import redeem
from apps.shipping.models import Governorate

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


def run_concurrently(target, count: int):
    """Run ``target(i)`` in ``count`` threads and collect (result, error)."""
    results: list = [None] * count
    errors: list = [None] * count
    barrier = threading.Barrier(count)

    def worker(index: int) -> None:
        try:
            barrier.wait(timeout=30)  # maximise real contention
            results[index] = target(index)
        except Exception as exc:  # noqa: BLE001 - recording, not swallowing
            errors[index] = exc
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return results, errors


class ConcurrencyBase(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        SiteSetting.objects.get_solo()
        self.governorate = Governorate.objects.create(key="cairo", name="القاهرة")
        self.category = Category.objects.create(
            slug="fingerprint", name="أقفال بالبصمة", status=PublicationStatus.PUBLISHED
        )
        self.product = Product.objects.create(
            slug="zakey-apex-pro",
            name="قفل زاكي أبيكس برو",
            category=self.category,
            status=PublicationStatus.PUBLISHED,
            published_at=timezone.now(),
        )
        self.variant = ProductVariant.objects.create(
            product=self.product,
            sku="ZK-APEX-OBSIDIAN",
            finish_label="أسود",
            price=Decimal("7490.00"),
            is_default=True,
        )

    def make_customer(self, index: int) -> CustomerProfile:
        user = User.objects.create_user(
            email=f"buyer{index}@example.com", password="StrongPass!234"
        )
        return CustomerProfile.objects.create(user=user, full_name=f"عميل {index}")

    def make_cart_with_one_unit(self, index: int) -> Cart:
        customer = self.make_customer(index)
        cart = Cart.objects.create(customer=customer)
        CartLine.objects.create(cart=cart, variant=self.variant, quantity=1)
        return cart


class TestNoOverselling(ConcurrencyBase):
    """SC-002: the last unit can only be sold once."""

    def test_twenty_concurrent_checkouts_for_one_unit(self):
        StockItem.objects.create(variant=self.variant, on_hand=1, reserved=0)
        shoppers = 20
        carts = [self.make_cart_with_one_unit(i) for i in range(shoppers)]

        def checkout(index: int):
            return create_order(
                cart=Cart.objects.get(pk=carts[index].pk),
                email=f"buyer{index}@example.com",
                phone="01012345678",
                address_data=dict(ADDRESS),
                idempotency_key=f"race-{index}",
                terms_accepted=True,
            )

        results, errors = run_concurrently(checkout, shoppers)

        succeeded = [r for r in results if r is not None]
        failed = [e for e in errors if e is not None]

        assert len(succeeded) == 1, f"expected exactly 1 order, got {len(succeeded)}"
        assert len(failed) == shoppers - 1
        assert Order.objects.count() == 1

        stock = StockItem.objects.get(variant=self.variant)
        assert stock.reserved == 1
        assert stock.available == 0
        assert stock.available >= 0, "available must never go negative (INV-001)"

    def test_available_never_negative_under_contention(self):
        StockItem.objects.create(variant=self.variant, on_hand=5, reserved=0)
        shoppers = 20
        carts = [self.make_cart_with_one_unit(i) for i in range(shoppers)]

        def checkout(index: int):
            return create_order(
                cart=Cart.objects.get(pk=carts[index].pk),
                email=f"buyer{index}@example.com",
                phone="01012345678",
                address_data=dict(ADDRESS),
                idempotency_key=f"race5-{index}",
                terms_accepted=True,
            )

        results, _ = run_concurrently(checkout, shoppers)
        succeeded = [r for r in results if r is not None]

        assert len(succeeded) == 5, f"5 units must yield exactly 5 orders, got {len(succeeded)}"
        stock = StockItem.objects.get(variant=self.variant)
        assert stock.reserved == 5
        assert stock.available == 0


class TestIdempotentCheckout(ConcurrencyBase):
    """SC-003: a replayed submission never creates a second order."""

    def test_same_idempotency_key_replayed_ten_times(self):
        StockItem.objects.create(variant=self.variant, on_hand=50, reserved=0)
        cart = self.make_cart_with_one_unit(0)

        def checkout(_index: int):
            return create_order(
                cart=Cart.objects.get(pk=cart.pk),
                email="buyer0@example.com",
                phone="01012345678",
                address_data=dict(ADDRESS),
                idempotency_key="one-and-only",
                terms_accepted=True,
            )

        results, _ = run_concurrently(checkout, 10)
        created = [r for r in results if r is not None]

        assert Order.objects.count() == 1, "a replay must not create a second order"
        numbers = {order.number for order in created}
        assert len(numbers) <= 1

        stock = StockItem.objects.get(variant=self.variant)
        assert stock.reserved == 1, "stock must be reserved once, not ten times"

    def test_sequential_replay_returns_the_same_order(self):
        StockItem.objects.create(variant=self.variant, on_hand=10, reserved=0)
        cart = self.make_cart_with_one_unit(0)

        first = create_order(
            cart=Cart.objects.get(pk=cart.pk),
            email="buyer0@example.com",
            phone="01012345678",
            address_data=dict(ADDRESS),
            idempotency_key="repeat-me",
            terms_accepted=True,
        )
        second = create_order(
            cart=Cart.objects.get(pk=cart.pk),
            email="buyer0@example.com",
            phone="01012345678",
            address_data=dict(ADDRESS),
            idempotency_key="repeat-me",
            terms_accepted=True,
        )
        assert first.pk == second.pk
        assert Order.objects.count() == 1


class TestCouponUsageRace(ConcurrencyBase):
    """SC-004: a coupon limited to 5 uses is redeemed exactly 5 times."""

    def test_twenty_concurrent_redemptions_of_a_five_use_coupon(self):
        StockItem.objects.create(variant=self.variant, on_hand=100, reserved=0)
        coupon = Coupon.objects.create(
            code="ZAKEYDEMO",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal("5"),
            usage_limit=5,
            is_demo=True,
        )
        attempts = 20
        orders = [
            Order.objects.create(
                number=f"ZK-C-{i}",
                email=f"buyer{i}@example.com",
                phone="01012345678",
                idempotency_key=f"coupon-{i}",
                subtotal=Decimal("1000.00"),
                grand_total=Decimal("950.00"),
            )
            for i in range(attempts)
        ]

        def try_redeem(index: int):
            with transaction.atomic():
                return redeem(coupon, orders[index], Decimal("50.00"))

        results, _ = run_concurrently(try_redeem, attempts)
        succeeded = [r for r in results if r is not None]

        coupon.refresh_from_db()
        assert len(succeeded) == 5, f"expected exactly 5 redemptions, got {len(succeeded)}"
        assert coupon.times_used == 5
        assert coupon.redemptions.count() == 5


class TestOrderNumberUniqueness(ConcurrencyBase):
    """Order numbers stay unique under contention (INV-007)."""

    def test_fifty_concurrent_orders_get_fifty_distinct_numbers(self):
        StockItem.objects.create(variant=self.variant, on_hand=100, reserved=0)
        shoppers = 50
        carts = [self.make_cart_with_one_unit(i) for i in range(shoppers)]

        def checkout(index: int):
            return create_order(
                cart=Cart.objects.get(pk=carts[index].pk),
                email=f"buyer{index}@example.com",
                phone="01012345678",
                address_data=dict(ADDRESS),
                idempotency_key=f"unique-{index}",
                terms_accepted=True,
            )

        results, _ = run_concurrently(checkout, shoppers)
        created = [r for r in results if r is not None]

        numbers = {order.number for order in created}
        assert len(numbers) == len(created), "order numbers collided"
        assert Order.objects.count() == len(created)


class TestMultiLineLockOrdering(ConcurrencyBase):
    """Deterministic lock order prevents the classic AB/BA deadlock."""

    def test_carts_with_reversed_variant_order_do_not_deadlock(self):
        second_variant = ProductVariant.objects.create(
            product=self.product,
            sku="ZK-APEX-CHAMPAGNE",
            finish_label="ذهبي",
            price=Decimal("7490.00"),
            position=1,
        )
        StockItem.objects.create(variant=self.variant, on_hand=50, reserved=0)
        StockItem.objects.create(variant=second_variant, on_hand=50, reserved=0)

        carts = []
        for i in range(10):
            customer = self.make_customer(i)
            cart = Cart.objects.create(customer=customer)
            order_of_variants = (
                [self.variant, second_variant] if i % 2 == 0 else [second_variant, self.variant]
            )
            for variant in order_of_variants:
                CartLine.objects.create(cart=cart, variant=variant, quantity=1)
            carts.append(cart)

        def checkout(index: int):
            return create_order(
                cart=Cart.objects.get(pk=carts[index].pk),
                email=f"buyer{index}@example.com",
                phone="01012345678",
                address_data=dict(ADDRESS),
                idempotency_key=f"deadlock-{index}",
                terms_accepted=True,
            )

        results, errors = run_concurrently(checkout, 10)
        succeeded = [r for r in results if r is not None]

        deadlocks = [e for e in errors if e and "deadlock" in str(e).lower()]
        assert not deadlocks, f"deadlock detected: {deadlocks}"
        assert len(succeeded) == 10, f"all 10 should complete, got {len(succeeded)}"


class TestStockAdjustDuringCheckout(ConcurrencyBase):
    """An admin adjustment and a checkout contend for the same row safely."""

    def test_no_negative_available_when_adjusting_during_checkout(self):
        StockItem.objects.create(variant=self.variant, on_hand=10, reserved=0)
        carts = [self.make_cart_with_one_unit(i) for i in range(8)]

        from apps.inventory.models import MovementReason
        from apps.inventory.services import adjust

        def work(index: int):
            if index == 0:
                return adjust(self.variant, -5, MovementReason.DAMAGED, note="تلف")
            return create_order(
                cart=Cart.objects.get(pk=carts[index].pk),
                email=f"buyer{index}@example.com",
                phone="01012345678",
                address_data=dict(ADDRESS),
                idempotency_key=f"adjust-{index}",
                terms_accepted=True,
            )

        run_concurrently(work, 8)

        stock = StockItem.objects.get(variant=self.variant)
        assert stock.available >= 0, "available went negative (INV-001 violated)"
        assert stock.reserved <= stock.on_hand


class TestCheckoutLocksTheStockRows(ConcurrencyBase):
    """*Where* the reservation happens, not merely what it adds up to.

    The oversell tests above prove the outcome is right. They would still pass
    if the reservation were serialised by some other mechanism — an advisory
    lock, a retry loop, luck. These two assert the mechanism itself: the
    checkout takes ``SELECT … FOR UPDATE`` on the stock row, and it does so
    inside the same transaction that writes the order.
    """

    def _checkout(self, cart, *, index: int, key: str):
        return create_order(
            cart=Cart.objects.get(pk=cart.pk),
            email=f"buyer{index}@example.com",
            phone="01012345678",
            address_data=dict(ADDRESS),
            idempotency_key=key,
            terms_accepted=True,
        )

    def test_checkout_waits_for_a_lock_held_on_the_stock_row(self):
        """FR-023: checkout blocks on the stock row's ``FOR UPDATE`` lock.

        A second connection holds the row and does nothing else. If checkout
        read the row without locking it, it would sail past; the assertion that
        it is still running proves it queued behind the lock. The control
        checkout immediately before it rules out the alternative explanation
        that a checkout is simply slow.
        """
        StockItem.objects.create(variant=self.variant, on_hand=5, reserved=0)
        control_cart = self.make_cart_with_one_unit(0)
        blocked_cart = self.make_cart_with_one_unit(1)

        started = time.monotonic()
        self._checkout(control_cart, index=0, key="lock-control")
        unblocked_seconds = time.monotonic() - started
        assert unblocked_seconds < 2, (
            f"an uncontended checkout took {unblocked_seconds:.1f}s; the block "
            "measured below would prove nothing"
        )

        lock_taken = threading.Event()
        may_release = threading.Event()

        def hold_the_stock_row() -> None:
            try:
                with transaction.atomic():
                    StockItem.objects.select_for_update().get(variant=self.variant)
                    lock_taken.set()
                    may_release.wait(timeout=30)
            finally:
                lock_taken.set()
                connections.close_all()

        holder = threading.Thread(target=hold_the_stock_row)
        holder.start()
        assert lock_taken.wait(timeout=10), "the holding thread never took the lock"

        finished = threading.Event()
        failures: list[BaseException] = []

        def blocked_checkout() -> None:
            try:
                self._checkout(blocked_cart, index=1, key="lock-blocked")
            except BaseException as exc:  # noqa: BLE001 - recorded, not swallowed
                failures.append(exc)
            finally:
                finished.set()
                connections.close_all()

        buyer = threading.Thread(target=blocked_checkout)
        buyer.start()
        try:
            assert not finished.wait(timeout=2), (
                "checkout finished while another transaction held SELECT ... FOR "
                "UPDATE on the stock row — it never locked the row"
            )
        finally:
            may_release.set()
            holder.join(timeout=30)

        assert finished.wait(timeout=30), "checkout never resumed after the lock lifted"
        buyer.join(timeout=30)
        assert not failures, f"the blocked checkout failed: {failures}"

        assert Order.objects.count() == 2
        stock = StockItem.objects.get(variant=self.variant)
        assert stock.reserved == 2

    def test_a_failure_after_reserving_rolls_the_reservation_back(self):
        """FR-023: the reservation is written inside the order transaction.

        Reserving in its own transaction would look identical while everything
        succeeds. Interrupting the checkout *after* the reservation is written
        tells the two apart: if the hold survives a rolled-back order, the stock
        is held for a customer who does not exist.
        """
        StockItem.objects.create(variant=self.variant, on_hand=5, reserved=0)
        cart = self.make_cart_with_one_unit(0)

        with mock.patch(
            "apps.orders.services.OrderEvent.objects.create",
            side_effect=RuntimeError("مقاطعة بعد الحجز"),
        ):
            with self.assertRaises(RuntimeError):
                self._checkout(cart, index=0, key="rollback-1")

        assert Order.objects.count() == 0, "the order survived its own failure"
        assert StockReservation.objects.count() == 0, "the hold outlived the order"
        assert StockMovement.objects.count() == 0, "a ledger row outlived the order"
        stock = StockItem.objects.get(variant=self.variant)
        assert (stock.on_hand, stock.reserved) == (5, 0)
