"""PostgreSQL concurrency evidence for money (SC-013, INV-004, FR-074).

The two scenarios the order/stock/coupon suite does not cover:

* a payment attempt replayed concurrently must produce **one** payment;
* concurrent refunds must never together exceed what was captured.

Real threads, real transactions, ``TransactionTestCase``. A sequential version
of either test would pass against a completely unlocked implementation, so it
would be no evidence at all.
"""

from __future__ import annotations

import threading
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase

from apps.orders.models import Order
from apps.payments import services
from apps.payments.models import Payment, PaymentMethod, PaymentState, Refund


def run_concurrently(target, count: int):
    """Run ``target(i)`` in ``count`` threads, released together."""
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


class PaymentConcurrencyBase(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        from apps.core.models import SiteSetting

        SiteSetting.objects.get_solo()
        self.method = PaymentMethod.objects.create(
            code="payment-cod",
            label="الدفع عند الاستلام",
            collects_on_delivery=True,
        )
        self.order = Order.objects.create(
            number="ZK-RACE-0001",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="race-order-1",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1000.00"),
        )


class TestPaymentIdempotencyRace(PaymentConcurrencyBase):
    """SC-013: one key, many simultaneous attempts, one payment."""

    def test_twenty_concurrent_attempts_with_one_key_create_one_payment(self):
        def attempt(_index: int):
            return services.record_payment(
                order=self.order,
                method=self.method,
                amount=Decimal("1000.00"),
                idempotency_key="same-key",
            )

        results, errors = run_concurrently(attempt, 20)

        self.assertEqual(
            Payment.objects.count(),
            1,
            "a replayed payment key created more than one payment row",
        )
        survivors = [r for r in results if r is not None]
        self.assertTrue(survivors, f"every attempt failed: {errors}")
        # Every thread that returned must have returned the same row.
        self.assertEqual(len({r.pk for r in survivors}), 1)

    def test_distinct_keys_create_distinct_attempts(self):
        """The guard must not collapse genuinely different attempts."""

        def attempt(index: int):
            return services.record_payment(
                order=self.order,
                method=self.method,
                amount=Decimal("100.00"),
                idempotency_key=f"key-{index}",
            )

        run_concurrently(attempt, 10)
        # 10 × 100 exactly exhausts the 1000 total, so all ten are legitimate.
        self.assertEqual(Payment.objects.count(), 10)


class TestRefundRace(PaymentConcurrencyBase):
    """INV-004: Σ refunds ≤ captured, under contention."""

    def setUp(self) -> None:
        super().setUp()
        payment = services.record_payment(
            order=self.order,
            method=self.method,
            amount=Decimal("1000.00"),
            idempotency_key="capture-me",
        )
        self.payment = services.capture(payment, reference="REF")

    def test_concurrent_refunds_cannot_exceed_the_captured_amount(self):
        """Ten threads each try to refund 200 of a 1000 capture.

        Five can legitimately succeed. Without the locked re-read they would all
        pass a check taken before any of them wrote, and refund 2000.

        This is FR-075's locked service check under real contention: the bound
        holds only because the remaining balance is read inside the row lock,
        and a sequential test would pass against a completely unlocked one.
        """

        def give_back(_index: int):
            return services.refund(self.payment, Decimal("200.00"), reason="سباق")

        results, errors = run_concurrently(give_back, 10)

        self.payment.refresh_from_db()
        total = self.payment.refunded_amount
        self.assertLessEqual(
            total,
            Decimal("1000.00"),
            f"refunded {total} against a 1000.00 capture (INV-004 breached)",
        )
        self.assertEqual(total, Decimal("1000.00"), "the five valid refunds did not all land")
        self.assertEqual(Refund.objects.count(), 5)
        self.assertEqual(self.payment.state, PaymentState.REFUNDED)
        # The five excess attempts are refused by one of two guards depending on
        # where they land in the race: `OverRefund` while a balance remains, and
        # the "not captured" guard once the payment has flipped to REFUNDED.
        # Both are correct refusals, so the assertion is on the count, not on
        # which of the two won.
        from django.core.exceptions import ValidationError

        refused = [e for e in errors if isinstance(e, ValidationError)]
        self.assertEqual(len(refused), 5, f"expected 5 refusals, got {errors}")

    def test_concurrent_full_refunds_leave_exactly_one(self):
        def give_back(_index: int):
            return services.refund(self.payment, Decimal("1000.00"), reason="كامل")

        run_concurrently(give_back, 8)

        self.payment.refresh_from_db()
        self.assertEqual(Refund.objects.count(), 1)
        self.assertEqual(self.payment.refunded_amount, Decimal("1000.00"))

    def test_reconciliation_sees_no_divergence_after_the_race(self):
        def give_back(_index: int):
            return services.refund(self.payment, Decimal("250.00"), reason="سباق")

        run_concurrently(give_back, 8)

        self.order.refresh_from_db()
        self.assertEqual(services.reconcile(self.order), [])
