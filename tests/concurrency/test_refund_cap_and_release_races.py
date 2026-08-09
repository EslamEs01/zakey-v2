"""PostgreSQL concurrency evidence for the two divergences closed in this pass.

* **FR-075** — the refund cap must hold when the *service is not in the path*.
  `test_payment_races.py` already proves the locked service check serialises
  concurrent refunds. That is a different claim: it says the service is correct,
  not that the invariant is. These tests write refunds straight through the ORM
  from many threads, so the only thing that can stop them is the constraint
  trigger and the ``SELECT ... FOR UPDATE`` inside it.

* **FR-025** — a hold must be released exactly once when the last payment
  attempt fails, even if two failure callbacks land simultaneously.

Real threads, real transactions, ``TransactionTestCase``. Run sequentially, every
test here would pass against a completely unlocked implementation.
"""

from __future__ import annotations

import threading
from decimal import Decimal

from django.db import connections
from django.test import TransactionTestCase

from apps.inventory import services as inventory_services
from apps.inventory.models import MovementReason, ReservationState, StockMovement
from apps.orders.models import Order
from apps.payments import services as payment_services
from apps.payments.models import Payment, PaymentMethod, PaymentState, Refund, RefundState


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


class RefundCapRaceBase(TransactionTestCase):
    reset_sequences = True

    def setUp(self) -> None:
        from apps.core.models import SiteSetting

        SiteSetting.objects.get_solo()
        self.method = PaymentMethod.objects.create(
            code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True
        )
        self.order = Order.objects.create(
            number="ZK-TRG-0001",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="trigger-race-1",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1000.00"),
        )
        self.payment = Payment.objects.create(
            order=self.order,
            method=self.method,
            amount=Decimal("1000.00"),
            state=PaymentState.CAPTURED,
            idempotency_key="trigger-race-pay-1",
        )


class TestTheTriggerStopsConcurrentOverRefund(RefundCapRaceBase):
    """FR-075: ten threads, no service, 1000.00 captured — 1000.00 refunded."""

    def test_concurrent_direct_writes_cannot_together_exceed_the_capture(self):
        def insert(index: int):
            Refund.objects.create(
                payment=self.payment,
                amount=Decimal("200.00"),
                reason=f"محاولة {index}",
                state=RefundState.COMPLETED,
            )
            return "accepted"

        results, errors = run_concurrently(insert, 10)

        accepted = [r for r in results if r == "accepted"]
        refused = [e for e in errors if e is not None]
        total = self.payment.refunded_amount

        assert total <= Decimal("1000.00"), f"the database allowed {total} against 1000.00"
        assert total == Decimal("1000.00"), "the cap was under-used; the lock over-serialised"
        assert len(accepted) == 5, f"expected 5 accepted, got {len(accepted)}"
        assert len(refused) == 5, f"expected 5 refused, got {len(refused)}"

    def test_the_refusals_come_from_the_database(self):
        """Not from a Python guard that a future refactor could delete."""
        from django.db import IntegrityError

        Refund.objects.create(
            payment=self.payment,
            amount=Decimal("900.00"),
            reason="أولى",
            state=RefundState.COMPLETED,
        )

        def insert(index: int):
            Refund.objects.create(
                payment=self.payment,
                amount=Decimal("200.00"),
                reason=f"محاولة {index}",
                state=RefundState.COMPLETED,
            )
            return "accepted"

        _results, errors = run_concurrently(insert, 6)

        raised = [e for e in errors if e is not None]
        assert raised, "every concurrent over-refund was accepted"
        assert all(isinstance(e, IntegrityError) for e in raised), (
            f"expected IntegrityError from the trigger, got {[type(e) for e in raised]}"
        )


class TestReleaseAfterFailureRace(TransactionTestCase):
    """FR-025: simultaneous failures release the hold exactly once."""

    reset_sequences = True

    def setUp(self) -> None:
        from apps.catalog.models import Category, Product, ProductVariant
        from apps.core.models import PublicationStatus, SiteSetting
        from apps.inventory.models import StockItem

        SiteSetting.objects.get_solo()
        self.method = PaymentMethod.objects.create(
            code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True
        )
        category = Category.objects.create(slug="race-cat", name="فئة")
        product = Product.objects.create(
            slug="race-product", name="منتج", category=category,
            status=PublicationStatus.PUBLISHED,
        )
        self.variant = ProductVariant.objects.create(
            product=product, sku="ZK-RACE-REL", finish_id="default", finish_label="",
            price=Decimal("500.00"), is_default=True,
        )
        self.stock = StockItem.objects.create(variant=self.variant, on_hand=10, reserved=0)
        self.order = Order.objects.create(
            number="ZK-REL-0001",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="release-race-1",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1000.00"),
        )
        inventory_services.reserve(self.variant, 2, order=self.order)
        self.payments = [
            payment_services.record_payment(
                order=self.order, method=self.method,
                amount=Decimal("500.00"), idempotency_key=f"release-race-pay-{i}",
            )
            for i in range(2)
        ]

    def _release_movements(self):
        return StockMovement.objects.filter(
            order=self.order, reason=MovementReason.RELEASE
        ).count()

    def test_two_simultaneous_failures_release_the_hold_once(self):
        """The order lock decides which failure is the last one."""

        def fail(index: int):
            payment_services.mark_failed(self.payments[index], reason=f"رفض {index}")
            return "failed"

        _results, errors = run_concurrently(fail, 2)

        assert [e for e in errors if e is not None] == []
        self.stock.refresh_from_db()
        assert self.stock.reserved == 0, "the hold survived both attempts failing"
        assert self._release_movements() == 1, "the ledger gained a duplicate release"
        assert self.order.reservations.get().state == ReservationState.RELEASED

    def test_the_same_failure_callback_delivered_four_times_at_once_releases_once(self):
        """FR-025 + FR-074: re-delivery converges, it does not accumulate."""
        payment_services.mark_failed(self.payments[1], reason="ثانية")
        self.stock.refresh_from_db()
        assert self.stock.reserved == 2, "guard: one live attempt should still remain"

        def replay(_index: int):
            payment_services.mark_failed(self.payments[0], reason="رفض مكرر")
            return "handled"

        _results, errors = run_concurrently(replay, 4)

        assert [e for e in errors if e is not None] == []
        self.stock.refresh_from_db()
        assert self.stock.reserved == 0
        assert self._release_movements() == 1
        assert self.order.events.filter(event_type="stock_released").count() == 1
