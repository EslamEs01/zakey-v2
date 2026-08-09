"""The movement-reason vocabulary, and which lifecycle event writes each one.

Two separate properties live here.

The first is the *vocabulary*: the ledger records a reason for every movement,
and that reason is drawn from a closed list. A tenth reason invented at some
call site would make the ledger unreadable — every report, filter and audit
query in the admin is written against this list, so a value outside it is
silently invisible rather than loudly wrong.

The second is *who writes which one*. ``reserve``, ``release`` and ``fulfill``
cannot be produced by a staff adjustment; they are written by the reservation
lifecycle, and the reason left behind is how the ledger says which of the
lifecycle's exits actually happened — a hold given back, or goods that left the
building.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.inventory import services
from apps.inventory.models import (
    MovementReason,
    ReservationState,
    StockMovement,
    StockReservation,
)
from apps.orders.models import Order, OrderStatus
from apps.orders.services import transition

pytestmark = pytest.mark.django_db

#: Copied by hand from the specification line, not imported from the code under
#: test. Deriving the expectation from ``MovementReason`` would make this test
#: agree with any list the code happens to hold.
SPEC_REASONS = {
    "purchase",
    "reserve",
    "release",
    "fulfill",
    "return",
    "adjust",
    "damaged",
    "lost",
    "correction",
}


def make_order(number: str = "ZK-MOV-1") -> Order:
    return Order.objects.create(
        number=number,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=f"idem-{number}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


def unsaved_movement(stock, reason: str) -> StockMovement:
    return StockMovement(
        stock_item=stock,
        delta=1,
        reason=reason,
        on_hand_before=stock.on_hand,
        on_hand_after=stock.on_hand + 1,
        reserved_before=stock.reserved,
        reserved_after=stock.reserved,
    )


class TestTheReasonVocabulary:
    """FR-022: nine reasons, exactly the nine the specification enumerates."""

    def test_the_enumeration_is_exactly_the_nine_named_reasons(self):
        assert set(MovementReason.values) == SPEC_REASONS
        assert len(MovementReason.values) == len(SPEC_REASONS) == 9

    def test_the_ledger_column_offers_no_other_choice(self):
        field = StockMovement._meta.get_field("reason")

        assert {value for value, _label in field.choices} == SPEC_REASONS

    def test_the_admin_adjustment_form_offers_no_other_choice(self):
        from apps.inventory.admin import StockAdjustForm

        offered = {value for value, _label in StockAdjustForm().fields["reason"].choices}

        assert offered == SPEC_REASONS

    def test_every_named_reason_is_accepted_by_the_ledger(self, stock):
        for reason in sorted(SPEC_REASONS):
            unsaved_movement(stock, reason).full_clean()

    def test_a_reason_outside_the_vocabulary_is_rejected_by_the_model(self, stock):
        with pytest.raises(ValidationError) as caught:
            unsaved_movement(stock, "shrinkage").full_clean()

        assert "reason" in caught.value.error_dict

    def test_the_service_layer_refuses_an_unknown_reason_and_writes_nothing(
        self, variant, stock
    ):
        before = stock.on_hand

        with pytest.raises(ValidationError):
            services.adjust(variant, 3, "shrinkage")

        stock.refresh_from_db()
        assert stock.on_hand == before
        assert not StockMovement.objects.exists()


class TestTheLifecycleWritesTheRightMovement:
    """The reasons only the reservation lifecycle can produce."""

    def test_reserving_writes_a_reserve_movement_and_moves_only_reserved(
        self, variant, stock
    ):
        services.reserve(variant, 3)

        movement = StockMovement.objects.latest("id")
        assert movement.reason == MovementReason.RESERVE
        assert movement.on_hand_before == movement.on_hand_after == stock.on_hand
        assert movement.reserved_after - movement.reserved_before == 3

    def test_cancelling_an_order_releases_its_reservations(self, variant, stock, user):
        """FR-025: a cancellation gives the hold back, as a `release` movement.

        Nothing is deducted: the goods never left, so ``on_hand`` must be
        exactly what it was before the checkout.
        """
        opening = stock.on_hand
        order = make_order("ZK-MOV-CANCEL")
        services.reserve(variant, 4, order=order)
        stock.refresh_from_db()
        assert stock.reserved == 4

        transition(order, OrderStatus.CANCELLED, actor=user)

        stock.refresh_from_db()
        assert stock.reserved == 0, "the hold was not given back"
        assert stock.on_hand == opening, "cancellation deducted stock that never shipped"
        assert (
            StockReservation.objects.get(order=order).state == ReservationState.RELEASED
        )
        release = StockMovement.objects.get(order=order, reason=MovementReason.RELEASE)
        assert release.reserved_before - release.reserved_after == 4

    def test_fulfilment_converts_the_reservation_into_a_deduction(
        self, variant, stock, user
    ):
        """FR-025: on fulfilment the hold stops being a hold and becomes a loss
        of real stock — ``reserved`` and ``on_hand`` both fall by the quantity.
        """
        opening = stock.on_hand
        order = make_order("ZK-MOV-FULFIL")
        services.reserve(variant, 3, order=order)

        transition(order, OrderStatus.CONFIRMED, actor=user)
        transition(order, OrderStatus.PROCESSING, actor=user)

        stock.refresh_from_db()
        assert stock.reserved == 0
        assert stock.on_hand == opening - 3, "fulfilment did not deduct the goods"
        assert (
            StockReservation.objects.get(order=order).state == ReservationState.CONSUMED
        )
        movement = StockMovement.objects.get(order=order, reason=MovementReason.FULFILL)
        assert movement.on_hand_before - movement.on_hand_after == 3
        assert movement.reserved_before - movement.reserved_after == 3

    def test_a_released_hold_can_never_afterwards_be_fulfilled(self, variant, stock):
        """FR-025: the two exits are exclusive.

        If a released reservation could still be fulfilled, the same three units
        would be given back to the pool *and* deducted from it.
        """
        opening = stock.on_hand
        reservation = services.reserve(variant, 3)
        services.release(reservation)

        with pytest.raises(ValidationError):
            services.fulfill(reservation)

        stock.refresh_from_db()
        assert stock.on_hand == opening
        assert stock.reserved == 0
