"""The two concurrency cases `test-strategy.md` §4 names that were missing.

* ``test_order_transition_concurrency`` — two staff act on one order at the same
  instant. Exactly one transition may win; the loser must be told its view of
  the order was stale, not silently succeed into a state the matrix forbids.
* ``test_reservation_expiry_idempotent`` — the expiry sweeper runs twice
  concurrently. The second pass must release nothing, or stock is handed back
  to the pool twice and the ledger stops balancing.

Both need real threads and real transactions, so ``TransactionTestCase`` rather
than ``TestCase`` — the latter wraps each test in a single transaction, which
hides every locking interaction and turns this file into a false negative.
"""

from __future__ import annotations

import threading
from datetime import timedelta
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase
from django.utils import timezone

from apps.accounts.models import User
from apps.catalog.models import Category, Product, ProductVariant
from apps.core.models import PublicationStatus, SiteSetting
from apps.inventory import services as inventory_services
from apps.inventory.models import ReservationState, StockItem, StockReservation
from apps.orders.models import InvalidTransition, Order, OrderStatus
from apps.orders.services import transition


def run_concurrently(target, count: int):
    """Run ``target(i)`` in ``count`` threads and collect (results, errors)."""
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


class RaceBase(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        SiteSetting.objects.get_solo()
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

    def make_order(self, status: str = OrderStatus.PENDING, number="ZK-RACE-1") -> Order:
        return Order.objects.create(
            number=number,
            email="nada@example.com",
            phone="01012345678",
            status=status,
            idempotency_key=f"key-{number}",
            subtotal=Decimal("7490.00"),
            grand_total=Decimal("7490.00"),
            placed_at=timezone.now(),
        )


class TestOrderTransitionConcurrency(RaceBase):
    """Two staff, one order, the same instant (INV-006, SC-005)."""

    def test_order_transition_concurrency(self):
        """Exactly one of two competing transitions wins (the §4 row).

        Both staff attempt the **same** edge. That is what makes the race
        decidable: once the first PENDING→CONFIRMED commits, the order is no
        longer PENDING, and CONFIRMED→CONFIRMED is not an edge in the matrix,
        so the loser must be refused rather than silently re-applying.

        Two *different* targets would not test this: PENDING→CONFIRMED followed
        by CONFIRMED→CANCELLED are both legal, so serialising them correctly
        produces two successes. That is the lock working, not failing.
        """
        order = self.make_order(OrderStatus.PENDING)
        staff = [
            User.objects.create_user(
                email=f"staff{i}@zakey.test", password="StrongPass!234", is_staff=True
            )
            for i in range(2)
        ]

        def act(index: int):
            return transition(
                Order.objects.get(pk=order.pk), OrderStatus.CONFIRMED, actor=staff[index]
            )

        results, errors = run_concurrently(act, 2)

        succeeded = [r for r in results if r is not None]
        failed = [e for e in errors if e is not None]

        assert len(succeeded) == 1, (
            f"expected exactly one winner, got {len(succeeded)}; "
            f"errors={[type(e).__name__ for e in failed]}"
        )
        assert len(failed) == 1, "the loser was not told its read was stale"
        assert isinstance(failed[0], InvalidTransition), (
            f"the loser got {type(failed[0]).__name__}, not a stale-state error"
        )

        order.refresh_from_db()
        assert order.status == OrderStatus.CONFIRMED

    def test_the_loser_leaves_no_event_behind(self):
        """A refused transition must not write history for something that
        did not happen."""
        from apps.orders.models import OrderEvent

        order = self.make_order(OrderStatus.PENDING, number="ZK-RACE-2")
        staff = [
            User.objects.create_user(
                email=f"ev{i}@zakey.test", password="StrongPass!234", is_staff=True
            )
            for i in range(2)
        ]

        def act(index: int):
            return transition(
                Order.objects.get(pk=order.pk), OrderStatus.CONFIRMED, actor=staff[index]
            )

        run_concurrently(act, 2)

        order.refresh_from_db()
        events = OrderEvent.objects.filter(order=order).exclude(to_status="")
        assert events.count() == 1, (
            f"expected one transition event, found {events.count()}"
        )
        assert events.first().to_status == order.status

    def test_divergent_targets_serialise_into_a_legal_sequence(self):
        """Different targets may both succeed — but only in a legal order.

        The property here is *no lost update*: whichever transition ran second
        must have been validated against the state the first one left behind,
        and each applied transition must have written exactly one event.
        """
        from apps.orders.models import ALLOWED_TRANSITIONS, OrderEvent

        order = self.make_order(OrderStatus.PENDING, number="ZK-RACE-4")
        staff = [
            User.objects.create_user(
                email=f"div{i}@zakey.test", password="StrongPass!234", is_staff=True
            )
            for i in range(2)
        ]
        targets = [OrderStatus.CONFIRMED, OrderStatus.CANCELLED]

        def act(index: int):
            return transition(
                Order.objects.get(pk=order.pk), targets[index], actor=staff[index]
            )

        results, _ = run_concurrently(act, 2)
        applied = len([r for r in results if r is not None])

        order.refresh_from_db()
        events = list(
            OrderEvent.objects.filter(order=order)
            .exclude(to_status="")
            .order_by("created_at", "id")
        )

        assert len(events) == applied, "an applied transition wrote no event, or vice versa"
        # Every recorded hop must be a real edge, walked from the real prior state.
        state = OrderStatus.PENDING
        for event in events:
            assert event.from_status == state, "a transition was validated against a stale read"
            assert event.to_status in ALLOWED_TRANSITIONS[state]
            state = event.to_status
        assert order.status == state

    def test_ten_way_contention_still_yields_one_winner(self):
        """Scaled up: ten staff, one order, one legal outcome."""
        order = self.make_order(OrderStatus.PENDING, number="ZK-RACE-3")
        actors = [
            User.objects.create_user(
                email=f"many{i}@zakey.test", password="StrongPass!234", is_staff=True
            )
            for i in range(10)
        ]

        def act(index: int):
            return transition(
                Order.objects.get(pk=order.pk), OrderStatus.CONFIRMED, actor=actors[index]
            )

        results, errors = run_concurrently(act, 10)

        assert len([r for r in results if r is not None]) == 1
        assert len([e for e in errors if e is not None]) == 9

        order.refresh_from_db()
        assert order.status == OrderStatus.CONFIRMED


class TestReservationExpiryIdempotent(RaceBase):
    """The sweeper must be safe to run twice (FR-024)."""

    def _expired_reservation(self) -> StockReservation:
        StockItem.objects.create(variant=self.variant, on_hand=10, reserved=0)
        reservation = inventory_services.reserve(self.variant, 3)
        StockReservation.objects.filter(pk=reservation.pk).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )
        return reservation

    def test_reservation_expiry_idempotent(self):
        """A second sequential run releases nothing."""
        self._expired_reservation()
        item = StockItem.objects.get(variant=self.variant)
        assert item.reserved == 3

        first = inventory_services.release_expired()
        second = inventory_services.release_expired()

        assert first == 1
        assert second == 0, "the sweeper released the same reservation twice"

        item.refresh_from_db()
        assert item.reserved == 0
        assert item.on_hand == 10, "stock was returned to the pool twice"

    def test_two_concurrent_sweeps_release_each_reservation_once(self):
        """The real race: two schedulers firing at the same instant.

        Without ``select_for_update`` plus the state re-check inside the lock,
        both passes would see the same ACTIVE row and both would decrement
        ``reserved`` — handing back stock that was only ever held once.
        """
        self._expired_reservation()

        results, errors = run_concurrently(lambda _: inventory_services.release_expired(), 2)

        assert not [e for e in errors if e is not None], (
            f"a concurrent sweep raised: {[e for e in errors if e]}"
        )
        assert sum(r for r in results if r) == 1, (
            "the same reservation was released by both sweeps"
        )

        item = StockItem.objects.get(variant=self.variant)
        assert item.reserved == 0
        assert item.on_hand == 10

    def test_the_ledger_balances_after_concurrent_sweeps(self):
        """Whatever the interleaving, the movement ledger must still reconcile."""
        self._expired_reservation()

        run_concurrently(lambda _: inventory_services.release_expired(), 4)

        drifts = inventory_services.verify_stock_integrity()
        assert drifts == [], f"concurrent sweeps left the ledger inconsistent: {drifts}"

    def test_an_active_reservation_is_never_swept(self):
        """Only *expired* reservations may be released."""
        StockItem.objects.create(variant=self.variant, on_hand=10, reserved=0)
        inventory_services.reserve(self.variant, 2)

        released = inventory_services.release_expired()

        assert released == 0
        item = StockItem.objects.get(variant=self.variant)
        assert item.reserved == 2
        assert (
            StockReservation.objects.filter(state=ReservationState.ACTIVE).count() == 1
        )
