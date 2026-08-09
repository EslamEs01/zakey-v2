"""The expiry sweeper command (T-0605, FR-024).

`tasks.md` names this command and it did not exist — only the service behind it
did. The runbook even schedules it in cron, so the gap would have surfaced as a
failing cron job on the first deploy.

Its literal acceptance criterion is "second run releases nothing".
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.inventory import services as inventory_services
from apps.inventory.models import ReservationState, StockItem, StockReservation

pytestmark = pytest.mark.django_db


def run(*args) -> str:
    out = StringIO()
    call_command("release_expired_reservations", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def expire(reservation) -> None:
    StockReservation.objects.filter(pk=reservation.pk).update(
        expires_at=timezone.now() - timedelta(hours=1)
    )


class TestTheSweep:
    def test_an_expired_reservation_is_released(self, variant, stock):
        """The expiry arm of FR-025: a hold that ran out is given back.

        The units return to the pool — ``reserved`` falls to zero — without any
        of them being deducted, because nothing was ever shipped.
        """
        opening = stock.on_hand
        reservation = inventory_services.reserve(variant, 3)
        expire(reservation)

        output = run()

        assert "released 1" in output
        reservation.refresh_from_db()
        # EXPIRED, not RELEASED: this sweep is time-driven, so the record says
        # the hold ran out. `reset_dev_state` records RELEASED because that is a
        # deliberate administrative act. The two must stay distinguishable in
        # the history.
        assert reservation.state == ReservationState.EXPIRED
        swept = StockItem.objects.get(pk=stock.pk)
        assert swept.reserved == 0
        assert swept.on_hand == opening, "expiry deducted stock that never shipped"

    def test_a_live_reservation_is_left_alone(self, variant, stock):
        """Only *expired* holds may be swept."""
        inventory_services.reserve(variant, 2)

        output = run()

        assert "released 0" in output
        assert StockItem.objects.get(pk=stock.pk).reserved == 2

    def test_the_second_run_releases_nothing(self, variant, stock):
        """T-0605's literal acceptance criterion."""
        reservation = inventory_services.reserve(variant, 2)
        expire(reservation)

        first = run()
        second = run()

        assert "released 1" in first
        assert "released 0" in second

    def test_stock_returns_to_the_shelf(self, variant, stock):
        before = StockItem.objects.get(pk=stock.pk).available
        reservation = inventory_services.reserve(variant, 4)
        assert StockItem.objects.get(pk=stock.pk).available == before - 4
        expire(reservation)

        run()

        assert StockItem.objects.get(pk=stock.pk).available == before

    def test_the_ledger_still_reconciles(self, variant, stock):
        reservation = inventory_services.reserve(variant, 3)
        expire(reservation)

        run()

        assert inventory_services.verify_stock_integrity() == []

    def test_it_sweeps_every_owner(self, variant, stock, customer):
        """Owner-blind by design: expiry applies to real customers too."""
        from apps.orders.models import Order

        order = Order.objects.create(
            number="ZK-EXP-1",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="key-exp-1",
            subtotal=Decimal("10.00"),
            grand_total=Decimal("10.00"),
        )
        reservation = inventory_services.reserve(variant, 2, order=order)
        expire(reservation)

        run()

        reservation.refresh_from_db()
        assert reservation.state == ReservationState.EXPIRED

    def test_batching_still_clears_everything(self, variant, stock):
        for _ in range(5):
            expire(inventory_services.reserve(variant, 1))

        run("--batch-size", "2")

        assert StockItem.objects.get(pk=stock.pk).reserved == 0
        assert (
            StockReservation.objects.filter(state=ReservationState.ACTIVE).count() == 0
        )

    def test_dry_run_changes_nothing(self, variant, stock):
        reservation = inventory_services.reserve(variant, 2)
        expire(reservation)

        output = run("--dry-run")

        assert "would release 1" in output
        assert StockItem.objects.get(pk=stock.pk).reserved == 2

    def test_json_output_is_parsable(self, variant, stock):
        expire(inventory_services.reserve(variant, 1))

        payload = json.loads(run("--json"))

        assert payload["released"] == 1
        assert payload["pending"] == 0

    def test_it_is_safe_with_nothing_to_do(self, stock):
        assert "released 0" in run()
