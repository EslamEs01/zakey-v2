"""Audited reconciliation of ledger discontinuities (FR-021, INV-001).

A break in the movement chain means something changed stock without recording
it. The ledger is append-only, so the break is permanent. The question this
mechanism answers is not "how do we make it go away" but "how does a human say,
on the record, that this specific gap is accounted for" — without also silencing
the next one.

These tests are mostly about what the mechanism must *refuse*.
"""

from __future__ import annotations

from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.inventory import services
from apps.inventory.models import StockItem, StockLedgerReconciliation, StockMovement

pytestmark = pytest.mark.django_db

REASON = "Development reset wrote reserved without a movement; incident closed."


def run(*args) -> str:
    out = StringIO()
    call_command("reconcile_stock_ledger", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


@pytest.fixture
def broken_chain(variant, stock):
    """Two movements with a manufactured discontinuity between them."""
    services.adjust(variant, 5, "purchase")
    services.adjust(variant, -2, "damaged")
    movements = list(
        StockMovement.objects.filter(stock_item=stock).order_by("created_at", "id")
    )
    first, second = movements[0], movements[1]
    # Simulate the original incident: a write that left no movement.
    StockMovement.objects.filter(pk=second.pk).update(
        on_hand_before=first.on_hand_after + 7
    )
    second.refresh_from_db()
    return StockItem.objects.get(pk=stock.pk), first, second


class TestTheBreakIsDetected:
    def test_an_unreconciled_break_is_reported(self, broken_chain):
        breaks = services.unreconciled_ledger_breaks()
        assert len(breaks) == 1
        assert breaks[0]["check"] == "ledger_chain"

    def test_the_integrity_command_fails_while_it_stands(self, broken_chain):
        with pytest.raises(CommandError):
            call_command("verify_stock_integrity", stdout=StringIO(), stderr=StringIO())


class TestReconciliation:
    def test_recording_an_explanation_clears_that_break(self, broken_chain):
        item, first, second = broken_chain

        services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )

        assert services.unreconciled_ledger_breaks() == []
        assert services.verify_stock_integrity() == []

    def test_the_movements_are_never_altered(self, broken_chain):
        item, first, second = broken_chain
        before = (
            first.on_hand_after, second.on_hand_before,
            StockMovement.objects.count(),
        )

        services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )

        first.refresh_from_db()
        second.refresh_from_db()
        assert (first.on_hand_after, second.on_hand_before,
                StockMovement.objects.count()) == before

    def test_the_explanation_is_preserved_and_attributable(self, broken_chain, user):
        item, first, second = broken_chain

        record = services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON, actor=user,
        )

        assert record.reason == REASON
        assert record.actor_id == user.pk
        assert record.observed_before == first.on_hand_after
        assert record.observed_after == second.on_hand_before

    def test_it_is_idempotent(self, broken_chain):
        item, first, second = broken_chain

        a = services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )
        b = services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason="different wording",
        )

        assert a.pk == b.pk
        assert StockLedgerReconciliation.objects.count() == 1

    def test_a_reconciliation_cannot_be_edited_or_deleted(self, broken_chain):
        item, first, second = broken_chain
        record = services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )

        with pytest.raises(ValidationError):
            record.save()
        with pytest.raises(ValidationError):
            record.delete()


class TestItCannotConcealOtherDrift:
    def test_a_second_unrelated_break_is_still_reported(self, broken_chain, variant):
        """The whole point: explaining one gap must not silence the next."""
        item, first, second = broken_chain
        services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )
        assert services.unreconciled_ledger_breaks() == []

        services.adjust(variant, 4, "purchase")
        movements = list(
            StockMovement.objects.filter(stock_item=item).order_by("created_at", "id")
        )
        StockMovement.objects.filter(pk=movements[-1].pk).update(
            on_hand_before=movements[-2].on_hand_after + 99
        )

        assert len(services.unreconciled_ledger_breaks()) == 1

    def test_it_does_not_hide_a_different_field_on_the_same_gap(self, broken_chain):
        item, first, second = broken_chain
        services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )
        StockMovement.objects.filter(pk=second.pk).update(
            reserved_before=first.reserved_after + 3
        )

        breaks = services.unreconciled_ledger_breaks()
        assert len(breaks) == 1
        assert "reserved" in breaks[0]["note"]

    def test_it_stops_applying_if_the_values_change(self, broken_chain):
        """Pinned to the reviewed values, not to the row identity."""
        item, first, second = broken_chain
        services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )
        assert services.unreconciled_ledger_breaks() == []

        StockMovement.objects.filter(pk=second.pk).update(
            on_hand_before=first.on_hand_after + 50
        )

        assert len(services.unreconciled_ledger_breaks()) == 1, (
            "the reconciliation absorbed a different discrepancy"
        )

    def test_it_does_not_mask_other_check_types(self, broken_chain, variant, stock):
        item, first, second = broken_chain
        services.reconcile_ledger_break(
            stock_item=item, field="on_hand",
            from_movement=first, to_movement=second, reason=REASON,
        )
        StockItem.objects.filter(pk=stock.pk).update(reserved=9)

        checks = {d["check"] for d in services.verify_stock_integrity()}
        assert "reserved_sum" in checks


class TestRefusals:
    def test_an_empty_reason_is_refused(self, broken_chain):
        item, first, second = broken_chain
        with pytest.raises(ValidationError):
            services.reconcile_ledger_break(
                stock_item=item, field="on_hand",
                from_movement=first, to_movement=second, reason="   ",
            )

    def test_reconciling_a_gap_that_does_not_exist_is_refused(self, variant, stock):
        services.adjust(variant, 3, "purchase")
        services.adjust(variant, 1, "purchase")
        movements = list(
            StockMovement.objects.filter(stock_item=stock).order_by("created_at", "id")
        )

        with pytest.raises(ValidationError) as caught:
            services.reconcile_ledger_break(
                stock_item=StockItem.objects.get(pk=stock.pk), field="on_hand",
                from_movement=movements[0], to_movement=movements[1], reason=REASON,
            )
        assert "انقطاع" in str(caught.value)

    def test_an_unknown_field_is_refused(self, broken_chain):
        item, first, second = broken_chain
        with pytest.raises(ValidationError):
            services.reconcile_ledger_break(
                stock_item=item, field="quantity",
                from_movement=first, to_movement=second, reason=REASON,
            )


class TestTheCommand:
    def test_it_reports_without_writing_by_default(self, broken_chain):
        output = run()

        assert "unreconciled ledger break" in output
        assert StockLedgerReconciliation.objects.count() == 0

    def test_apply_without_a_reason_is_refused(self, broken_chain):
        with pytest.raises(CommandError) as caught:
            run("--apply")

        assert "--reason is required" in str(caught.value)
        assert StockLedgerReconciliation.objects.count() == 0

    def test_apply_with_a_reason_records_and_clears(self, broken_chain):
        output = run("--apply", "--reason", REASON)

        assert "recorded 1" in output
        assert StockLedgerReconciliation.objects.count() == 1
        assert services.verify_stock_integrity() == []

    def test_running_twice_records_nothing_new(self, broken_chain):
        run("--apply", "--reason", REASON)
        second = run("--apply", "--reason", REASON)

        assert "No unreconciled ledger breaks" in second
        assert StockLedgerReconciliation.objects.count() == 1

    def test_a_clean_ledger_needs_no_reconciliation(self, variant, stock):
        services.adjust(variant, 3, "purchase")

        assert "No unreconciled ledger breaks" in run()
