"""The refund cap is enforced by the database, not by the service (FR-075, INV-004).

FR-075 asks for "a database constraint **plus** a locked service check". The
service check was there; the database half was not. That mattered more than a
wording quibble: `handoff.md` §2 states the project's own rule — load-bearing
invariants are enforced by a constraint "rather than by convention alone" — and
`reserved <= on_hand` really is. Refunds are the money-*losing* invariant, and
until now the only thing standing between ZAKEY and paying a customer twice was
a function that any other write path bypasses.

A plain ``CheckConstraint`` cannot express this. The bound is an aggregate over
sibling rows compared against a column on the parent, and a ``CHECK`` sees only
the row in front of it. So the mechanism is a ``CONSTRAINT TRIGGER`` created in
``payments/migrations/0002``.

Every test below writes **around** `payments.services.refund` on purpose. A test
that went through the service would prove the service works, which was never in
doubt.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.db import IntegrityError, connection, transaction

from apps.orders.models import Order
from apps.payments.models import Payment, PaymentMethod, PaymentState, Refund, RefundState

pytestmark = pytest.mark.django_db

TRIGGER = "refund_never_exceeds_capture"


@pytest.fixture
def method(db):
    return PaymentMethod.objects.create(
        code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True
    )


@pytest.fixture
def captured(db, method):
    """A captured payment of 1000.00 — so 1000.00 is refundable, and no more."""
    order = Order.objects.create(
        number="ZK-CAP-0001",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="cap-1",
        subtotal=Decimal("1000.00"),
        grand_total=Decimal("1000.00"),
    )
    return Payment.objects.create(
        order=order,
        method=method,
        amount=Decimal("1000.00"),
        state=PaymentState.CAPTURED,
        idempotency_key="cap-pay-1",
    )


def _refund(payment, amount: str, state: str = RefundState.COMPLETED) -> Refund:
    return Refund.objects.create(
        payment=payment, amount=Decimal(amount), reason="اختبار", state=state
    )


class TestTheConstraintExists:
    def test_the_migration_installed_a_constraint_trigger(self):
        """Proves 0002 actually ran on this freshly-migrated database.

        The test database is built by running every migration from empty, so a
        trigger visible here is a trigger a clean deploy gets.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT t.tgconstraint <> 0, c.relname
                  FROM pg_trigger t
                  JOIN pg_class c ON c.oid = t.tgrelid
                 WHERE t.tgname = %s AND NOT t.tgisinternal
                """,
                [TRIGGER],
            )
            row = cursor.fetchone()

        assert row is not None, f"{TRIGGER} is missing from the database"
        is_constraint_trigger, table = row
        assert is_constraint_trigger, "it must be a CONSTRAINT TRIGGER, not a plain one"
        assert table == "payments_refund"


class TestTheCapCannotBeBypassed:
    def test_a_direct_orm_create_over_the_cap_is_refused(self, captured):
        """FR-075: the ORM is not a way around it."""
        _refund(captured, "700.00")

        with pytest.raises(IntegrityError), transaction.atomic():
            _refund(captured, "400.00")

    def test_bulk_create_over_the_cap_is_refused(self, captured):
        """FR-075: ``bulk_create`` skips ``save()`` entirely — and still cannot pass."""
        with pytest.raises(IntegrityError), transaction.atomic():
            Refund.objects.bulk_create(
                [
                    Refund(
                        payment=captured,
                        amount=Decimal("600.00"),
                        reason="دفعة أولى",
                        state=RefundState.COMPLETED,
                    ),
                    Refund(
                        payment=captured,
                        amount=Decimal("600.00"),
                        reason="دفعة ثانية",
                        state=RefundState.COMPLETED,
                    ),
                ]
            )

        assert captured.refunds.count() == 0

    def test_raw_sql_over_the_cap_is_refused(self, captured):
        """FR-075: the strongest bypass — no Django in the path at all."""
        _refund(captured, "1000.00")

        with pytest.raises(IntegrityError), transaction.atomic(), connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO payments_refund
                    (payment_id, amount, reason, state, provider_reference,
                     created_at, updated_at)
                VALUES (%s, %s, 'تجاوز', 'completed', '', NOW(), NOW())
                """,
                [captured.pk, Decimal("0.01")],
            )

    def test_an_update_that_lifts_a_refund_over_the_cap_is_refused(self, captured):
        """FR-075: the trigger fires on UPDATE too, not only INSERT."""
        record = _refund(captured, "100.00")

        with pytest.raises(IntegrityError), transaction.atomic():
            Refund.objects.filter(pk=record.pk).update(amount=Decimal("1000.01"))

    def test_flipping_a_pending_refund_to_completed_over_the_cap_is_refused(self, captured):
        """FR-075: only completed refunds count, and completing one is checked.

        A pending refund parked below the line, then completed after the cap has
        been used up, is the obvious way to sneak past a check that only runs on
        insert.
        """
        _refund(captured, "1000.00")
        parked = _refund(captured, "50.00", state=RefundState.PENDING)

        with pytest.raises(IntegrityError), transaction.atomic():
            Refund.objects.filter(pk=parked.pk).update(state=RefundState.COMPLETED)

    def test_a_refund_against_an_uncaptured_payment_is_refused(self, captured):
        """FR-075: "captured minus already-refunded" — nothing captured, nothing refundable."""
        captured.state = PaymentState.PENDING
        captured.save(update_fields=["state"])

        with pytest.raises(IntegrityError), transaction.atomic():
            _refund(captured, "1.00")

    def test_many_small_refunds_are_stopped_at_the_line(self, captured):
        """FR-075: the aggregate is what is bounded, not any single refund."""
        for _ in range(10):
            _refund(captured, "100.00")

        assert captured.refunded_amount == Decimal("1000.00")

        with pytest.raises(IntegrityError), transaction.atomic():
            _refund(captured, "0.01")


class TestValidRefundsStillWork:
    def test_partial_refunds_below_the_cap_are_accepted(self, captured):
        _refund(captured, "250.00")
        _refund(captured, "125.50")

        assert captured.refunded_amount == Decimal("375.50")

    def test_refunding_exactly_the_captured_amount_is_allowed(self, captured):
        """The bound is ``<=``; refusing the last piastre would strand money."""
        _refund(captured, "999.99")
        _refund(captured, "0.01")

        assert captured.refunded_amount == Decimal("1000.00")

    def test_a_pending_refund_does_not_consume_the_cap(self, captured):
        _refund(captured, "1000.00", state=RefundState.PENDING)

        _refund(captured, "1000.00")

        assert captured.refunded_amount == Decimal("1000.00")

    def test_a_failed_refund_does_not_consume_the_cap(self, captured):
        _refund(captured, "1000.00", state=RefundState.FAILED)

        _refund(captured, "1000.00")

        assert captured.refunded_amount == Decimal("1000.00")

    def test_two_payments_have_independent_caps(self, captured, method):
        """The bound is per payment; one payment's refunds cannot exhaust another's."""
        other = Payment.objects.create(
            order=captured.order,
            method=method,
            amount=Decimal("500.00"),
            state=PaymentState.CAPTURED,
            idempotency_key="cap-pay-2",
        )
        _refund(captured, "1000.00")

        _refund(other, "500.00")

        assert other.refunded_amount == Decimal("500.00")

    def test_the_service_still_raises_a_readable_error_before_the_database_does(
        self, captured
    ):
        """The friendly error stays; the trigger is the authority behind it (FR-075)."""
        from apps.payments import services

        _refund(captured, "1000.00")

        with pytest.raises(services.OverRefund) as raised:
            services.refund(captured, Decimal("10.00"), reason="تجاوز")

        assert "يتجاوز" in str(raised.value)
