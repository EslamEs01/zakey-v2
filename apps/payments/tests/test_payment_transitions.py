"""Payment state machine, exhaustively (T-1803, SC-005, INV-004).

``tests/orders/test_transitions.py`` does this for orders. This is the other
half of "100% of order **and payment** transitions exercised": every
(current, target) pair in the payment matrix, not only the handful the happy
path happens to walk.

The Cartesian sweep is the point. A matrix tested only where someone remembered
to look is a matrix with unknown holes, and a hole in a *payment* state machine
is money moving in a way nobody modelled.
"""

from __future__ import annotations

import itertools
from decimal import Decimal

import pytest

from apps.payments.models import (
    ALLOWED_PAYMENT_TRANSITIONS,
    Payment,
    PaymentMethod,
    PaymentState,
)

pytestmark = pytest.mark.django_db

ALL_STATES = [choice for choice, _ in PaymentState.choices]

TERMINAL = {PaymentState.FAILED, PaymentState.CANCELLED, PaymentState.REFUNDED}


@pytest.fixture
def method(db):
    return PaymentMethod.objects.create(
        code="cod", label="الدفع عند الاستلام", is_active=True
    )


@pytest.fixture
def order(db):
    from apps.orders.models import Order

    return Order.objects.create(
        number="ZK-PAY-1",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="key-pay-1",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


def make_payment(order, method, state: str) -> Payment:
    return Payment.objects.create(
        order=order,
        method=method,
        state=state,
        amount=Decimal("7490.00"),
        currency="EGP",
    )


# ---------------------------------------------------------------------------
# The matrix is complete and self-consistent
# ---------------------------------------------------------------------------


class TestTheMatrixItself:
    def test_every_state_has_an_entry(self):
        assert set(ALLOWED_PAYMENT_TRANSITIONS) == set(ALL_STATES)

    def test_terminal_states_allow_nothing_further(self):
        for state in TERMINAL:
            assert ALLOWED_PAYMENT_TRANSITIONS[state] == frozenset(), (
                f"{state} is terminal but declares outgoing edges"
            )

    def test_every_target_is_a_real_state(self):
        for state, targets in ALLOWED_PAYMENT_TRANSITIONS.items():
            unknown = set(targets) - set(ALL_STATES)
            assert unknown == set(), f"{state} points at unknown states {unknown}"

    def test_capture_can_only_lead_to_a_refund(self):
        assert ALLOWED_PAYMENT_TRANSITIONS[PaymentState.CAPTURED] == frozenset(
            {PaymentState.PARTIALLY_REFUNDED, PaymentState.REFUNDED}
        )

    def test_a_partial_refund_may_repeat_or_complete(self):
        """Several partial refunds may follow one another until fully refunded."""
        assert ALLOWED_PAYMENT_TRANSITIONS[PaymentState.PARTIALLY_REFUNDED] == frozenset(
            {PaymentState.PARTIALLY_REFUNDED, PaymentState.REFUNDED}
        )

    def test_money_cannot_be_captured_after_failing(self):
        """The edge that would let a failed charge quietly become a real one."""
        assert PaymentState.CAPTURED not in ALLOWED_PAYMENT_TRANSITIONS[
            PaymentState.FAILED
        ]

    def test_a_cancelled_payment_cannot_be_revived(self):
        assert ALLOWED_PAYMENT_TRANSITIONS[PaymentState.CANCELLED] == frozenset()


# ---------------------------------------------------------------------------
# 100% of (current, target) pairs — the literal SC-005 requirement
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "current,target", list(itertools.product(ALL_STATES, ALL_STATES))
)
def test_full_cartesian_product_of_payment_transitions(
    order, method, current, target
):
    """Every pair behaves exactly as the matrix declares, with no exceptions."""
    payment = make_payment(order, method, current)
    expected = target in ALLOWED_PAYMENT_TRANSITIONS[current]

    assert payment.can_transition_to(target) is expected, (
        f"{current} -> {target}: model says {payment.can_transition_to(target)}, "
        f"matrix says {expected}"
    )


@pytest.mark.parametrize("state", ALL_STATES)
def test_no_state_can_transition_to_itself_except_partial_refund(order, method, state):
    """Self-transitions are a common way to double-apply an effect.

    Only PARTIALLY_REFUNDED legitimately repeats, because a second partial
    refund is a genuinely new event.
    """
    payment = make_payment(order, method, state)
    allowed = payment.can_transition_to(state)

    if state == PaymentState.PARTIALLY_REFUNDED:
        assert allowed is True
    else:
        assert allowed is False, f"{state} may transition to itself"


@pytest.mark.parametrize("state", sorted(TERMINAL))
def test_no_edge_leaves_a_terminal_state(order, method, state):
    payment = make_payment(order, method, state)

    reachable = [t for t in ALL_STATES if payment.can_transition_to(t)]

    assert reachable == [], f"{state} is terminal but can reach {reachable}"


# ---------------------------------------------------------------------------
# Reachability: the matrix must describe a usable machine
# ---------------------------------------------------------------------------


class TestReachability:
    def test_every_state_is_reachable_from_pending(self):
        """A state nothing can reach is dead code in a money machine."""
        seen = {PaymentState.PENDING}
        frontier = [PaymentState.PENDING]
        while frontier:
            state = frontier.pop()
            for target in ALLOWED_PAYMENT_TRANSITIONS[state]:
                if target not in seen:
                    seen.add(target)
                    frontier.append(target)

        unreachable = set(ALL_STATES) - seen
        assert unreachable == set(), f"unreachable payment states: {unreachable}"

    def test_every_non_terminal_state_can_still_move(self):
        for state in ALL_STATES:
            if state in TERMINAL:
                continue
            assert ALLOWED_PAYMENT_TRANSITIONS[state], (
                f"{state} is non-terminal but has no outgoing edge — a payment "
                "could get stuck there forever"
            )

    def test_a_refund_is_reachable_only_after_a_capture(self):
        """Refunding money that was never captured is INV-004's whole concern."""
        for state in ALL_STATES:
            if state in {PaymentState.CAPTURED, PaymentState.PARTIALLY_REFUNDED}:
                continue
            targets = ALLOWED_PAYMENT_TRANSITIONS[state]
            assert PaymentState.REFUNDED not in targets, (
                f"{state} can reach REFUNDED without passing through CAPTURED"
            )
            assert PaymentState.PARTIALLY_REFUNDED not in targets
