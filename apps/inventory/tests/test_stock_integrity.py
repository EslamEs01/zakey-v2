"""Stock integrity verification (T-0606, FR-027, FR-021).

Two properties matter here and they pull against each other:

* the command must **detect** every way the ledger, the reservations and the
  stored balances can disagree;
* the command must **never write**, whatever it finds.

Drift is manufactured with ``QuerySet.update()`` and direct field writes, which
is legitimate *inside a test that is simulating corruption* — ``StockMovement``
refuses edits through ``save()`` precisely so production code cannot do this.
"""

from __future__ import annotations

import json
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.inventory import services
from apps.inventory.models import (
    ReservationState,
    StockItem,
    StockMovement,
    StockReservation,
)

pytestmark = pytest.mark.django_db


def run(*args, **kwargs) -> str:
    out = StringIO()
    call_command("verify_stock_integrity", *args, stdout=out, stderr=StringIO(), **kwargs)
    return out.getvalue()


@pytest.fixture
def moved_stock(db, variant, stock):
    """A stock item with a real, consistent ledger behind it."""
    services.adjust(variant, 5, "purchase")
    services.adjust(variant, -2, "damaged")
    stock.refresh_from_db()
    return stock


# ---------------------------------------------------------------------------
# Clean data
# ---------------------------------------------------------------------------


class TestCleanData:
    def test_a_consistent_item_reports_no_drift(self, moved_stock):
        assert services.verify_stock_integrity() == []
        assert "No stock drift found" in run()

    def test_an_item_with_no_movements_is_not_drift(self, stock):
        """A seeded opening balance is legitimate, not a hole in the ledger."""
        assert stock.on_hand == 25
        assert not StockMovement.objects.filter(stock_item=stock).exists()

        assert services.verify_stock_integrity() == []

    def test_an_active_reservation_matching_reserved_is_clean(self, variant, stock):
        services.reserve(variant, 3)

        assert services.verify_stock_integrity() == []


# ---------------------------------------------------------------------------
# Each drift class is detected
# ---------------------------------------------------------------------------


class TestDriftDetection:
    def test_a_broken_ledger_chain_is_detected(self, moved_stock):
        oldest = StockMovement.objects.filter(stock_item=moved_stock).order_by(
            "created_at", "id"
        ).first()
        StockMovement.objects.filter(pk=oldest.pk).update(
            on_hand_after=oldest.on_hand_after + 7
        )

        checks = {d["check"] for d in services.verify_stock_integrity()}
        assert "ledger_chain" in checks

    def test_a_ledger_head_disagreeing_with_the_balance_is_detected(self, moved_stock):
        StockItem.objects.filter(pk=moved_stock.pk).update(on_hand=moved_stock.on_hand + 3)

        drifts = services.verify_stock_integrity()
        assert any(d["check"] == "ledger_head" for d in drifts)

    def test_reserved_disagreeing_with_active_reservations_is_detected(
        self, variant, stock
    ):
        services.reserve(variant, 3)
        StockReservation.objects.filter(stock_item=stock).update(quantity=9)

        drifts = services.verify_stock_integrity()
        assert any(d["check"] == "reserved_sum" for d in drifts)

    def test_a_stale_active_reservation_is_reported(self, variant, stock):
        services.reserve(variant, 2)
        StockReservation.objects.filter(stock_item=stock).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )

        drifts = services.verify_stock_integrity()
        assert any(d["check"] == "stale_reservation" for d in drifts)

    def test_a_swept_reservation_is_not_stale(self, variant, stock):
        services.reserve(variant, 2)
        StockReservation.objects.filter(stock_item=stock).update(
            expires_at=timezone.now() - timedelta(hours=1)
        )
        services.release_expired()

        drifts = services.verify_stock_integrity()
        assert not any(d["check"] == "stale_reservation" for d in drifts)

    def test_a_negative_balance_is_detected(self, stock):
        # Bypasses the CheckConstraint deliberately? No — it cannot be bypassed,
        # so this asserts the constraint is the thing standing in the way.
        from django.db.utils import IntegrityError

        with pytest.raises(IntegrityError):
            StockItem.objects.filter(pk=stock.pk).update(on_hand=-1)


# ---------------------------------------------------------------------------
# The command never mutates — the load-bearing guarantee
# ---------------------------------------------------------------------------


class TestTheCommandNeverWrites:
    def test_running_against_drifted_data_changes_nothing(self, moved_stock, variant):
        services.reserve(variant, 3)
        # Manufacture drift of several kinds at once.
        StockItem.objects.filter(pk=moved_stock.pk).update(on_hand=999)
        StockReservation.objects.filter(stock_item=moved_stock).update(quantity=42)

        before = {
            "items": list(
                StockItem.objects.order_by("pk").values("pk", "on_hand", "reserved")
            ),
            "movements": list(
                StockMovement.objects.order_by("pk").values(
                    "pk", "on_hand_before", "on_hand_after", "reserved_before", "reserved_after"
                )
            ),
            "reservations": list(
                StockReservation.objects.order_by("pk").values("pk", "quantity", "state")
            ),
        }

        with pytest.raises(CommandError):
            run()

        after = {
            "items": list(
                StockItem.objects.order_by("pk").values("pk", "on_hand", "reserved")
            ),
            "movements": list(
                StockMovement.objects.order_by("pk").values(
                    "pk", "on_hand_before", "on_hand_after", "reserved_before", "reserved_after"
                )
            ),
            "reservations": list(
                StockReservation.objects.order_by("pk").values("pk", "quantity", "state")
            ),
        }

        assert after == before, "the verifier repaired data instead of reporting it"

    def test_it_writes_no_movement_rows(self, moved_stock):
        StockItem.objects.filter(pk=moved_stock.pk).update(on_hand=999)
        before = StockMovement.objects.count()

        with pytest.raises(CommandError):
            run()

        assert StockMovement.objects.count() == before

    def test_there_is_no_repair_flag(self):
        """A ``--fix`` would be the whole failure mode; it must not exist."""
        with pytest.raises(CommandError):
            call_command("verify_stock_integrity", "--fix", stdout=StringIO())


# ---------------------------------------------------------------------------
# Command interface
# ---------------------------------------------------------------------------


class TestCommandInterface:
    def test_drift_makes_the_command_exit_non_zero(self, moved_stock):
        StockItem.objects.filter(pk=moved_stock.pk).update(on_hand=999)

        with pytest.raises(CommandError):
            run()

    def test_json_output_matches_the_human_run(self, moved_stock):
        StockItem.objects.filter(pk=moved_stock.pk).update(on_hand=999)
        expected = len(services.verify_stock_integrity())

        out = StringIO()
        with pytest.raises(CommandError):
            call_command("verify_stock_integrity", "--json", stdout=out, stderr=StringIO())

        payload = json.loads(out.getvalue())
        assert len(payload["drift"]) == expected

    def test_sku_scoping_excludes_other_variants(
        self, variant, stock, second_variant, second_stock
    ):
        StockItem.objects.filter(pk=second_stock.pk).update(on_hand=-0)
        services.adjust(second_variant, 4, "purchase")
        StockItem.objects.filter(pk=second_stock.pk).update(on_hand=987)

        # Unscoped: the drift is visible.
        assert services.verify_stock_integrity() != []
        # Scoped to the clean SKU: it is not.
        assert services.verify_stock_integrity(sku=variant.sku) == []

    def test_an_unknown_sku_is_an_error(self, stock):
        with pytest.raises(CommandError):
            run("--sku", "NO-SUCH-SKU")

    def test_scoped_clean_run_succeeds(self, variant, stock, second_variant, second_stock):
        services.adjust(second_variant, 4, "purchase")
        StockItem.objects.filter(pk=second_stock.pk).update(on_hand=987)

        assert "No stock drift found" in run("--sku", variant.sku)


# ---------------------------------------------------------------------------
# Low-stock reporting (FR-027)
# ---------------------------------------------------------------------------


class TestLowStockReport:
    def test_an_item_below_threshold_is_listed(self, variant, stock, site_setting):
        StockItem.objects.filter(pk=stock.pk).update(
            on_hand=2, low_stock_threshold=5
        )

        report = services.low_stock_report()

        assert [entry["sku"] for entry in report] == [variant.sku]
        assert report[0]["state"] == "low_stock"

    def test_an_out_of_stock_item_is_listed_as_such(self, variant, stock, site_setting):
        StockItem.objects.filter(pk=stock.pk).update(on_hand=0, low_stock_threshold=5)

        assert services.low_stock_report()[0]["state"] == "out_of_stock"

    def test_a_healthy_item_is_not_listed(self, stock, site_setting):
        StockItem.objects.filter(pk=stock.pk).update(low_stock_threshold=1)

        assert services.low_stock_report() == []

    def test_low_stock_alone_does_not_fail_the_command(self, stock, site_setting):
        StockItem.objects.filter(pk=stock.pk).update(on_hand=1, low_stock_threshold=5)

        output = run("--low-stock")

        assert "No stock drift found" in output
        assert "threshold" in output

    def test_the_per_item_threshold_overrides_the_site_default(
        self, variant, stock, site_setting
    ):
        StockItem.objects.filter(pk=stock.pk).update(on_hand=3, low_stock_threshold=None)
        default_says_low = services.low_stock_report()

        StockItem.objects.filter(pk=stock.pk).update(low_stock_threshold=1)
        override_says_healthy = services.low_stock_report()

        assert default_says_low != override_says_healthy
