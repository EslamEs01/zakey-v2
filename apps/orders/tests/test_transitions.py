"""Order state machine (FR-068, INV-006, SC-005).

Covers the **full Cartesian product** of statuses: every allowed edge succeeds
and every one of the remaining pairs is rejected. That is what 100% transition
coverage means here.
"""

from __future__ import annotations

import itertools
from decimal import Decimal

import pytest

from apps.orders.models import (
    ALLOWED_TRANSITIONS,
    TERMINAL_STATUSES,
    Order,
    OrderStatus,
)

pytestmark = pytest.mark.django_db

ALL_STATUSES = [choice for choice, _ in OrderStatus.choices]


def make_order(status: str, number: str = "ZK-TEST-1") -> Order:
    return Order.objects.create(
        number=number,
        email="nada@example.com",
        phone="01012345678",
        status=status,
        idempotency_key=f"key-{number}-{status}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


class TestTransitionMatrixIsComplete:
    def test_every_status_has_an_entry(self):
        assert set(ALLOWED_TRANSITIONS) == set(ALL_STATUSES)

    def test_terminal_statuses_allow_nothing(self):
        for status in TERMINAL_STATUSES - {OrderStatus.DELIVERED}:
            assert ALLOWED_TRANSITIONS[status] == frozenset()

    def test_delivered_only_leads_to_refunded(self):
        assert ALLOWED_TRANSITIONS[OrderStatus.DELIVERED] == frozenset(
            {OrderStatus.REFUNDED}
        )


@pytest.mark.parametrize("current,target", list(itertools.product(ALL_STATUSES, ALL_STATUSES)))
def test_full_cartesian_product_of_transitions(current, target):
    """Every (current, target) pair behaves exactly as the matrix says."""
    order = make_order(current, number=f"ZK-{current}-{target}")
    expected = target in ALLOWED_TRANSITIONS[current]
    assert order.can_transition_to(target) is expected


class TestRejectedTransitionsInDetail:
    @pytest.mark.parametrize(
        "current,target",
        [
            (OrderStatus.PENDING, OrderStatus.DELIVERED),   # skipping the pipeline
            (OrderStatus.PENDING, OrderStatus.SHIPPED),
            (OrderStatus.PENDING, OrderStatus.PROCESSING),
            (OrderStatus.SHIPPED, OrderStatus.PENDING),     # backwards
            (OrderStatus.DELIVERED, OrderStatus.SHIPPED),
            (OrderStatus.CANCELLED, OrderStatus.CONFIRMED), # out of a terminal state
            (OrderStatus.REFUNDED, OrderStatus.DELIVERED),
            (OrderStatus.CONFIRMED, OrderStatus.DELIVERED),
        ],
    )
    def test_invalid_transition_is_refused(self, current, target):
        order = make_order(current, number=f"ZK-BAD-{current}-{target}")
        assert order.can_transition_to(target) is False

    def test_no_status_can_transition_to_itself(self):
        for status in ALL_STATUSES:
            order = make_order(status, number=f"ZK-SELF-{status}")
            assert order.can_transition_to(status) is False


class TestAllowedTransitions:
    @pytest.mark.parametrize(
        "current,target",
        [
            (OrderStatus.PENDING, OrderStatus.CONFIRMED),
            (OrderStatus.PENDING, OrderStatus.CANCELLED),
            (OrderStatus.CONFIRMED, OrderStatus.PROCESSING),
            (OrderStatus.CONFIRMED, OrderStatus.CANCELLED),
            (OrderStatus.PROCESSING, OrderStatus.SHIPPED),
            (OrderStatus.PROCESSING, OrderStatus.CANCELLED),
            (OrderStatus.SHIPPED, OrderStatus.DELIVERED),
            (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
            (OrderStatus.DELIVERED, OrderStatus.REFUNDED),
        ],
    )
    def test_valid_transition_is_permitted(self, current, target):
        order = make_order(current, number=f"ZK-OK-{current}-{target}")
        assert order.can_transition_to(target) is True

    def test_cancellation_is_reachable_from_every_pre_delivery_state(self):
        for status in (
            OrderStatus.PENDING,
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
        ):
            order = make_order(status, number=f"ZK-CANCEL-{status}")
            assert order.can_transition_to(OrderStatus.CANCELLED) is True


class TestCustomerCancellationWindow:
    """A customer may only cancel early; staff may cancel later (§4)."""

    @pytest.mark.parametrize(
        "status,expected",
        [
            (OrderStatus.PENDING, True),
            (OrderStatus.CONFIRMED, True),
            (OrderStatus.PROCESSING, False),
            (OrderStatus.SHIPPED, False),
            (OrderStatus.DELIVERED, False),
            (OrderStatus.CANCELLED, False),
            (OrderStatus.REFUNDED, False),
        ],
    )
    def test_customer_cancel_window(self, status, expected):
        order = make_order(status, number=f"ZK-CC-{status}")
        assert order.customer_can_cancel is expected


class TestOrderSnapshotsAreImmutable:
    """INV-003: order lines never change after creation."""

    def test_order_line_cannot_be_edited(self, variant, stock):
        from django.core.exceptions import ValidationError

        from apps.orders.models import OrderLine

        order = make_order(OrderStatus.PENDING, number="ZK-SNAP-1")
        line = OrderLine.objects.create(
            order=order,
            variant=variant,
            product_name="قفل زاكي أبيكس برو",
            sku=variant.sku,
            unit_price=Decimal("7490.00"),
            quantity=1,
            line_total=Decimal("7490.00"),
        )
        line.unit_price = Decimal("1.00")
        with pytest.raises(ValidationError):
            line.save()

    def test_order_line_cannot_be_deleted(self, variant, stock):
        from django.core.exceptions import ValidationError

        from apps.orders.models import OrderLine

        order = make_order(OrderStatus.PENDING, number="ZK-SNAP-2")
        line = OrderLine.objects.create(
            order=order,
            variant=variant,
            product_name="قفل زاكي أبيكس برو",
            sku=variant.sku,
            unit_price=Decimal("7490.00"),
            quantity=1,
            line_total=Decimal("7490.00"),
        )
        with pytest.raises(ValidationError):
            line.delete()

    def test_archiving_a_variant_keeps_the_line_readable(self, variant, stock):
        """FR-067: history survives catalogue change."""
        from apps.orders.models import OrderLine

        order = make_order(OrderStatus.PENDING, number="ZK-SNAP-3")
        line = OrderLine.objects.create(
            order=order,
            variant=variant,
            product_name="قفل زاكي أبيكس برو",
            sku=variant.sku,
            unit_price=Decimal("7490.00"),
            quantity=1,
            line_total=Decimal("7490.00"),
        )
        # Snapshot values are independent of the live catalogue record.
        variant.product.name = "اسم مختلف تمامًا"
        variant.product.save()
        line.refresh_from_db()
        assert line.product_name == "قفل زاكي أبيكس برو"
        assert line.unit_price == Decimal("7490.00")


class TestIdempotencyKeyIsUnique:
    def test_duplicate_idempotency_key_rejected(self):
        """INV-002: one confirmed order per key."""
        from django.db import IntegrityError, transaction

        Order.objects.create(
            number="ZK-IDEM-1",
            email="a@example.com",
            phone="01012345678",
            idempotency_key="same-key",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
        )
        with pytest.raises(IntegrityError), transaction.atomic():
            Order.objects.create(
                number="ZK-IDEM-2",
                email="a@example.com",
                phone="01012345678",
                idempotency_key="same-key",
                subtotal=Decimal("100.00"),
                grand_total=Decimal("100.00"),
            )


class TestEveryStatusChangeIsRecorded:
    """The order history is written by the transition, not alongside it."""

    def test_each_status_change_writes_an_event_naming_who_what_and_when(self, user):
        """FR-069: actor, from-state, to-state and timestamp on every change.

        One order is walked the length of the pipeline and the events are read
        back as a trail: one event per change, in order, each one saying where
        the order came from, where it went, who moved it and when. A missing or
        blank ``from_status`` would leave a history that cannot be replayed.
        """
        from apps.orders.models import OrderEvent
        from apps.orders.services import transition

        order = make_order(OrderStatus.PENDING, number="ZK-EVT-1")
        walk = [
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
            OrderStatus.REFUNDED,
        ]

        previous = OrderStatus.PENDING
        for target in walk:
            transition(order, target, actor=user)
            order.refresh_from_db()
            assert order.status == target

            event = OrderEvent.objects.filter(order=order, to_status=target).get()
            assert event.event_type == "status_change"
            assert event.from_status == previous
            assert event.to_status == target
            assert event.actor_id == user.pk
            assert event.created_at is not None
            previous = target

        trail = list(
            OrderEvent.objects.filter(order=order, event_type="status_change")
            .order_by("created_at", "id")
            .values_list("from_status", "to_status")
        )
        assert trail == list(zip([OrderStatus.PENDING, *walk], walk))

    def test_the_note_is_optional_and_stored_verbatim_when_given(self, user):
        """FR-069: an optional note, recorded as written.

        Staff explain awkward transitions in their own words; a note that is
        silently dropped or truncated is worse than no note field at all.
        """
        from apps.orders.models import OrderEvent
        from apps.orders.services import transition

        order = make_order(OrderStatus.PENDING, number="ZK-EVT-NOTE")

        transition(order, OrderStatus.CONFIRMED, actor=user)
        assert OrderEvent.objects.get(order=order, to_status=OrderStatus.CONFIRMED).note == ""

        reason = "العميل طلب التأجيل حتى نهاية الأسبوع."
        transition(order, OrderStatus.CANCELLED, actor=user, note=reason)
        assert OrderEvent.objects.get(order=order, to_status=OrderStatus.CANCELLED).note == reason

    def test_a_refused_transition_records_nothing(self, user):
        """FR-069: only *changes* are recorded.

        An attempt that the state machine rejected did not change the order, so
        writing an event for it would put a change in the history that never
        happened.
        """
        from apps.orders.models import InvalidTransition, OrderEvent
        from apps.orders.services import transition

        order = make_order(OrderStatus.PENDING, number="ZK-EVT-BAD")

        with pytest.raises(InvalidTransition):
            transition(order, OrderStatus.DELIVERED, actor=user)

        order.refresh_from_db()
        assert order.status == OrderStatus.PENDING
        assert not OrderEvent.objects.filter(order=order).exists()

    def test_an_event_cannot_be_rewritten_or_removed(self, user):
        """FR-069: the trail is append-only, or it is not a record."""
        from django.core.exceptions import ValidationError

        from apps.orders.models import OrderEvent
        from apps.orders.services import transition

        order = make_order(OrderStatus.PENDING, number="ZK-EVT-APPEND")
        transition(order, OrderStatus.CONFIRMED, actor=user)
        event = OrderEvent.objects.get(order=order)

        event.note = "تعديل لاحق"
        with pytest.raises(ValidationError):
            event.save()
        with pytest.raises(ValidationError):
            event.delete()

    def test_staff_notes_and_customer_visible_notes_stay_apart(self, user):
        """FR-069: the two kinds of note are distinguishable rows, and the
        internal one is the default.

        Staff write things customers must not read. If visibility were a
        convention rather than a stored flag — or if it defaulted to visible —
        an internal remark would reach the customer the first time somebody
        forgot to say otherwise.
        """
        from apps.orders.models import OrderNote

        order = make_order(OrderStatus.PENDING, number="ZK-NOTE-1")

        internal = OrderNote.objects.create(
            order=order, author=user, body="العميل تأخر في السداد سابقًا."
        )
        published = OrderNote.objects.create(
            order=order,
            author=user,
            body="سنتواصل معك لتأكيد موعد التسليم.",
            is_customer_visible=True,
        )

        assert internal.is_customer_visible is False, "notes are internal unless published"
        assert published.is_customer_visible is True

        visible = set(order.notes.filter(is_customer_visible=True).values_list("pk", flat=True))
        assert visible == {published.pk}
        assert internal.pk not in visible

        # …and the status history is a third, separate record: publishing a note
        # never moves an order, and a transition note is not a customer note.
        from apps.orders.services import transition

        transition(order, OrderStatus.CONFIRMED, actor=user, note="ملاحظة داخلية على الانتقال")
        assert order.notes.count() == 2
        assert order.notes.filter(is_customer_visible=True).count() == 1
