"""Returned goods, and the human decision that decides where they go.

A refund is a money event. Whether the parcel actually came back, and whether
what came back is sellable, is a judgement someone standing next to the box
makes — a lock with a scratched fascia, a box opened and repacked, a unit that
was never posted at all. No amount of order or payment state can infer it.

So the rule under test is a *negative* one, and negatives rot quietly: the way
this breaks is that somebody later adds a helpful signal on refund, or on the
``returned`` fulfilment status, and inventory starts inventing stock that
nobody has seen. Most of this file exists to make that change fail loudly.

The positive half is small by comparison: restocking is one explicit call, it
records who decided, and writing the goods off instead is a different, equally
recorded act.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.inventory import services
from apps.inventory.models import MovementReason, StockMovement
from apps.orders.models import FulfillmentStatus, Order, OrderStatus
from apps.orders.services import transition
from apps.payments import services as payment_services
from apps.payments.models import PaymentMethod

pytestmark = pytest.mark.django_db

TOTAL = Decimal("7490.00")


@pytest.fixture
def cod(db):
    return PaymentMethod.objects.create(
        code="payment-cod",
        label="الدفع عند الاستلام",
        collects_on_delivery=True,
    )


@pytest.fixture
def fulfilled_order(db, variant, stock, user):
    """An order whose two units have really left the building.

    Fulfilment is what makes a return interesting: ``on_hand`` has already been
    deducted, so putting the goods back is an *addition*, and an addition that
    happened by itself is stock that does not exist.
    """
    order = Order.objects.create(
        number="ZK-RET-1",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="idem-ZK-RET-1",
        subtotal=TOTAL,
        grand_total=TOTAL,
    )
    services.reserve(variant, 2, order=order)
    order = transition(order, OrderStatus.CONFIRMED, actor=user)
    order = transition(order, OrderStatus.PROCESSING, actor=user)

    stock.refresh_from_db()
    assert stock.on_hand == 23, "the fixture did not actually deduct the goods"
    return order


class TestNothingRestocksAutomatically:
    """FR-028: returned stock never goes back on the shelf by itself."""

    def test_refunding_the_payment_does_not_restock(
        self, fulfilled_order, stock, cod, user
    ):
        payment = payment_services.record_payment(
            order=fulfilled_order,
            method=cod,
            amount=TOTAL,
            idempotency_key="ret-pay-1",
            actor=user,
        )
        payment = payment_services.capture(payment, reference="REF-RET-1", actor=user)
        movements_before = StockMovement.objects.count()

        payment_services.refund(payment, TOTAL, reason="مرتجع من العميل", actor=user)

        stock.refresh_from_db()
        assert stock.on_hand == 23, "the refund put stock back without anyone deciding"
        assert StockMovement.objects.count() == movements_before
        assert not StockMovement.objects.filter(reason=MovementReason.RETURN).exists()

    def test_moving_the_order_to_refunded_does_not_restock(
        self, fulfilled_order, stock, user
    ):
        order = transition(fulfilled_order, OrderStatus.SHIPPED, actor=user)
        order = transition(order, OrderStatus.DELIVERED, actor=user)
        movements_before = StockMovement.objects.count()

        order = transition(order, OrderStatus.REFUNDED, actor=user)

        assert order.status == OrderStatus.REFUNDED
        stock.refresh_from_db()
        assert stock.on_hand == 23
        assert StockMovement.objects.count() == movements_before

    def test_cancelling_after_fulfilment_does_not_put_the_goods_back(
        self, fulfilled_order, stock, user
    ):
        """Cancelling releases *holds*. Goods that already shipped are not a
        hold, and cancellation must not conjure them back."""
        movements_before = StockMovement.objects.count()

        transition(fulfilled_order, OrderStatus.CANCELLED, actor=user)

        stock.refresh_from_db()
        assert stock.on_hand == 23
        assert stock.reserved == 0
        assert StockMovement.objects.count() == movements_before

    def test_marking_the_order_returned_writes_no_stock_movement(
        self, fulfilled_order, stock
    ):
        """The fulfilment status is a label on the order, not an instruction to
        inventory. A signal wired to it would fail here."""
        movements_before = StockMovement.objects.count()

        fulfilled_order.fulfillment_status = FulfillmentStatus.RETURNED
        fulfilled_order.save(update_fields=["fulfillment_status", "updated_at"])

        stock.refresh_from_db()
        assert stock.on_hand == 23
        assert StockMovement.objects.count() == movements_before


class TestTheStaffDecision:
    """The only route back onto the shelf, and the alternative to taking it."""

    def test_restocking_is_an_explicit_call_that_records_who_decided(
        self, fulfilled_order, variant, stock, user
    ):
        """FR-028: putting the goods back is one deliberate, attributed act."""
        services.restock_return(variant, 2, actor=user, note="فُحص وقُبل للبيع")

        stock.refresh_from_db()
        assert stock.on_hand == 25, "the explicit restock did not put the goods back"
        movement = StockMovement.objects.get(reason=MovementReason.RETURN)
        assert movement.delta == 2
        assert movement.actor_id == user.pk, "the decision has no author"
        assert movement.note == "فُحص وقُبل للبيع"

    def test_restock_and_write_off_are_separately_recorded(
        self, fulfilled_order, variant, stock, user
    ):
        """FR-028: restock and write-off are two decisions, not one default.

        Both units came back; one is sellable and one is not. The ledger has to
        be able to tell the two decisions apart afterwards.
        """
        services.restock_return(variant, 1, actor=user, note="سليم")
        services.adjust(variant, -1, MovementReason.DAMAGED, actor=user, note="مرتجع تالف")

        stock.refresh_from_db()
        assert stock.on_hand == 23, "the written-off unit was still counted as sellable"
        recent = list(
            StockMovement.objects.order_by("-id").values_list("reason", flat=True)[:2]
        )
        assert recent == [MovementReason.DAMAGED, MovementReason.RETURN]

    def test_restocking_a_non_positive_quantity_is_refused(self, variant, stock):
        for quantity in (0, -3):
            with pytest.raises(ValidationError):
                services.restock_return(variant, quantity)

        stock.refresh_from_db()
        assert stock.on_hand == 25
        assert not StockMovement.objects.exists()
