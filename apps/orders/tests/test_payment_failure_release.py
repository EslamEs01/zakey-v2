"""A failed payment gives the stock back (FR-025).

``inventory-integrity.md`` §3 draws the edge that these tests defend:

```
active ──cancel / payment fail──► released
```

Before this, only *cancel* and *TTL expiry* were wired up: a failed payment left
the hold ``active`` until staff noticed or the sweeper ran an hour later, so a
customer whose card was declined kept someone else's stock off the shelf.

The interesting half is what must **not** happen. ``failed`` is terminal per
*attempt* (``payment-state-machine.md`` §2), and a retry is a new ``Payment``
row, so an order can hold a failed attempt and a live one simultaneously.
Releasing on the first failure would take the basket away from a customer who is
still paying.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.inventory import services as inventory_services
from apps.inventory.models import MovementReason, ReservationState, StockMovement
from apps.orders import services as order_services
from apps.orders.models import Order
from apps.payments import services as payment_services
from apps.payments.models import PaymentMethod, PaymentState

pytestmark = pytest.mark.django_db


@pytest.fixture
def method(db):
    return PaymentMethod.objects.create(
        code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True
    )


def _order(number: str = "ZK-FAIL-0001", key: str = "fail-1") -> Order:
    return Order.objects.create(
        number=number,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=key,
        subtotal=Decimal("1000.00"),
        grand_total=Decimal("1000.00"),
    )


@pytest.fixture
def held(variant, stock, site_setting, method):
    """An order holding two units of real stock, with one pending attempt."""
    order = _order()
    inventory_services.reserve(variant, 2, order=order)
    payment = payment_services.record_payment(
        order=order, method=method, amount=Decimal("1000.00"), idempotency_key="pay-1"
    )
    stock.refresh_from_db()
    assert stock.reserved == 2
    return order, payment, stock


def _release_movements(order) -> list[StockMovement]:
    return list(
        StockMovement.objects.filter(order=order, reason=MovementReason.RELEASE).order_by("id")
    )


class TestATerminalFailureReleasesTheHold:
    def test_the_reservation_is_released_and_the_stock_comes_back(self, held):
        """FR-025: the only live attempt fails, so the hold ends."""
        order, payment, stock = held

        payment_services.mark_failed(payment, reason="رفض البنك")

        stock.refresh_from_db()
        assert stock.reserved == 0, "the failed payment left the stock held"
        reservation = order.reservations.get()
        assert reservation.state == ReservationState.RELEASED

    def test_the_release_is_recorded_in_the_append_only_ledger(self, held):
        """FR-025: the balance is never edited behind the ledger's back.

        The movement must carry the before/after snapshots, because
        ``verify_stock_integrity`` reconstructs the balance from those and would
        report drift for a release that only decremented the column.
        """
        order, payment, stock = held

        payment_services.mark_failed(payment, reason="رفض البنك")

        movements = _release_movements(order)
        assert len(movements) == 1
        movement = movements[0]
        assert movement.delta == -2
        assert movement.reserved_before == 2
        assert movement.reserved_after == 0
        assert movement.on_hand_before == movement.on_hand_after, "a release must not move on_hand"
        assert inventory_services.verify_stock_integrity(sku=stock.variant.sku) == []

    def test_an_order_event_records_why_the_stock_moved(self, held):
        order, payment, _ = held

        payment_services.mark_failed(payment, reason="رفض البنك")

        assert order.events.filter(event_type="stock_released").count() == 1


class TestALiveAttemptKeepsTheHold:
    def test_a_failure_alongside_a_pending_retry_releases_nothing(self, held, method):
        """FR-025: one attempt failing is not the *order* failing to pay.

        The customer mistyped a number and is trying again. Releasing here would
        hand their stock to somebody else mid-checkout.
        """
        order, first, stock = held
        payment_services.record_payment(
            order=order, method=method, amount=Decimal("1000.00"), idempotency_key="pay-2"
        )

        payment_services.mark_failed(first, reason="رفض البنك")

        stock.refresh_from_db()
        assert stock.reserved == 2, "the retry's hold was taken away"
        assert order.reservations.get().state == ReservationState.ACTIVE
        assert _release_movements(order) == []

    def test_the_hold_ends_only_when_the_last_attempt_fails(self, held, method):
        """FR-025: the release happens on the transition to *no* live attempt."""
        order, first, stock = held
        second = payment_services.record_payment(
            order=order, method=method, amount=Decimal("1000.00"), idempotency_key="pay-2"
        )

        payment_services.mark_failed(first, reason="أولى")
        stock.refresh_from_db()
        assert stock.reserved == 2

        payment_services.mark_failed(second, reason="ثانية")

        stock.refresh_from_db()
        assert stock.reserved == 0
        assert len(_release_movements(order)) == 1

    def test_a_captured_payment_keeps_the_hold_even_if_a_later_attempt_fails(
        self, variant, stock, site_setting, method
    ):
        """FR-025: money moved, so the goods stay committed to this order.

        A part-paid order — 600 captured, the remaining 400 declined. Fulfilment
        converts the reservation to a deduction; releasing it here would let the
        shop sell stock a customer has already partly paid for.
        """
        order = _order(number="ZK-FAIL-0004", key="fail-4")
        inventory_services.reserve(variant, 2, order=order)
        paid = payment_services.record_payment(
            order=order, method=method, amount=Decimal("600.00"), idempotency_key="pay-part-1"
        )
        payment_services.capture(paid)
        rest = payment_services.record_payment(
            order=order, method=method, amount=Decimal("400.00"), idempotency_key="pay-part-2"
        )

        payment_services.mark_failed(rest, reason="رفض الباقي")

        stock.refresh_from_db()
        assert stock.reserved == 2, "stock was released although money had been captured"
        assert order.reservations.get().state == ReservationState.ACTIVE
        assert _release_movements(order) == []


class TestReplaysAndScope:
    def test_a_duplicate_failure_callback_releases_nothing_the_second_time(self, held):
        """FR-025: idempotent under re-delivery (FR-074).

        A provider re-sending the same failure must converge to the same state,
        not release a second time — which, once another order had reserved the
        freed unit, would corrupt *their* balance.
        """
        order, payment, stock = held

        payment_services.mark_failed(payment, reason="رفض البنك")
        payment_services.mark_failed(payment, reason="رفض البنك")
        payment_services.mark_failed(payment, reason="رفض البنك")

        stock.refresh_from_db()
        assert stock.reserved == 0
        assert len(_release_movements(order)) == 1, "the ledger gained a phantom release"
        assert order.events.filter(event_type="stock_released").count() == 1

    def test_a_replayed_failure_appends_no_second_payment_event(self, held):
        order, payment, _ = held

        payment_services.mark_failed(payment, reason="رفض البنك")
        payment_services.mark_failed(payment, reason="رفض البنك")

        assert payment.events.filter(event_type="failed").count() == 1

    def test_it_cannot_release_another_order_s_reservation(
        self, held, second_variant, second_stock, method
    ):
        """FR-025: the release is scoped to the failing order's own hold."""
        order, payment, stock = held
        neighbour = _order(number="ZK-FAIL-0002", key="fail-2")
        inventory_services.reserve(second_variant, 3, order=neighbour)

        payment_services.mark_failed(payment, reason="رفض البنك")

        second_stock.refresh_from_db()
        assert second_stock.reserved == 3, "another order's stock was released"
        assert neighbour.reservations.get().state == ReservationState.ACTIVE
        assert _release_movements(neighbour) == []

    def test_releasing_after_cancellation_does_not_double_release(self, held):
        """FR-025 meets §2.5: double release is guarded by reservation state."""
        order, payment, stock = held
        order_services.transition(order, "cancelled")
        stock.refresh_from_db()
        assert stock.reserved == 0

        payment_services.mark_failed(payment, reason="رفض بعد الإلغاء")

        stock.refresh_from_db()
        assert stock.reserved == 0
        assert len(_release_movements(order)) == 1


class TestTheServiceItself:
    def test_it_reports_how_many_reservations_it_released(self, held):
        order, payment, _ = held
        payment_services.mark_failed(payment, reason="رفض")

        assert order_services.release_reservations_after_payment_failure(order) == 0, (
            "a second call must find nothing left to release"
        )

    def test_it_refuses_to_act_while_an_attempt_is_still_pending(self, held):
        order, _payment, stock = held

        assert order_services.release_reservations_after_payment_failure(order) == 0

        stock.refresh_from_db()
        assert stock.reserved == 2
        assert order.reservations.get().state == ReservationState.ACTIVE

    def test_a_payment_that_never_existed_leaves_a_bare_order_alone(
        self, variant, stock, site_setting
    ):
        """An order with no attempts at all has nothing to fail, so nothing releases."""
        order = _order(number="ZK-FAIL-0003", key="fail-3")
        inventory_services.reserve(variant, 1, order=order)

        released = order_services.release_reservations_after_payment_failure(order)

        assert released == 1, "no live attempt exists, so the hold is stale"
        stock.refresh_from_db()
        assert stock.reserved == 0


def test_the_failed_state_is_still_terminal(held):
    """Guard: the release must not have loosened the payment machine (FR-073)."""
    _order_, payment, _stock = held
    payment_services.mark_failed(payment, reason="رفض")

    with pytest.raises(payment_services.InvalidPaymentTransition):
        payment_services.capture(payment)

    payment.refresh_from_db()
    assert payment.state == PaymentState.FAILED
