"""Stock integrity (FR-020, FR-026, FR-029, INV-001).

These assert the **database** refuses bad states. That distinction is the whole
point of FR-029: integrity must survive an application bug, a shell session, a
data import or a careless admin action.
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.inventory.models import MovementReason, StockItem, StockMovement

pytestmark = pytest.mark.django_db


class TestDatabaseEnforcesStockInvariant:
    def test_reserved_cannot_exceed_on_hand(self, stock):
        """INV-001 enforced by CheckConstraint, not by application code."""
        stock.reserved = stock.on_hand + 1
        with pytest.raises(IntegrityError), transaction.atomic():
            stock.save()

    def test_on_hand_cannot_go_negative(self, stock):
        stock.on_hand = -1
        with pytest.raises(IntegrityError), transaction.atomic():
            stock.save()

    def test_reserved_cannot_go_negative(self, stock):
        stock.reserved = -1
        with pytest.raises(IntegrityError), transaction.atomic():
            stock.save()

    def test_reserved_equal_to_on_hand_is_allowed(self, stock):
        """The boundary is legal - everything reserved, nothing available."""
        stock.reserved = stock.on_hand
        stock.save()
        stock.refresh_from_db()
        assert stock.available == 0

    def test_raw_sql_cannot_bypass_the_constraint(self, stock):
        """Even bypassing the ORM entirely cannot oversell."""
        from django.db import connection

        with pytest.raises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE inventory_stockitem SET reserved = on_hand + 5 WHERE id = %s",
                    [stock.pk],
                )


class TestDerivedQuantities:
    def test_available_is_on_hand_minus_reserved(self, stock):
        stock.on_hand, stock.reserved = 10, 4
        stock.save()
        assert stock.available == 6

    def test_low_stock_uses_site_setting_when_unset(self, stock, site_setting):
        site_setting.low_stock_threshold = 5
        site_setting.save()
        stock.on_hand, stock.reserved = 5, 0
        stock.save()
        assert stock.effective_low_stock_threshold == 5
        assert stock.is_low_stock is True

    def test_per_item_threshold_overrides_the_site_default(self, stock):
        stock.low_stock_threshold = 2
        stock.on_hand, stock.reserved = 5, 0
        stock.save()
        assert stock.effective_low_stock_threshold == 2
        assert stock.is_low_stock is False

    def test_out_of_stock_when_everything_is_reserved(self, stock):
        stock.reserved = stock.on_hand
        stock.save()
        assert stock.is_out_of_stock is True


class TestMovementLedgerIsAppendOnly:
    """FR-021: the ledger has no update or delete path, for anyone."""

    def _movement(self, stock):
        return StockMovement.objects.create(
            stock_item=stock,
            delta=5,
            reason=MovementReason.PURCHASE,
            on_hand_before=stock.on_hand,
            on_hand_after=stock.on_hand + 5,
            reserved_before=stock.reserved,
            reserved_after=stock.reserved,
        )

    def test_movement_cannot_be_updated(self, stock):
        movement = self._movement(stock)
        movement.delta = 999
        with pytest.raises(ValidationError):
            movement.save()

    def test_movement_cannot_be_deleted(self, stock):
        movement = self._movement(stock)
        with pytest.raises(ValidationError):
            movement.delete()

    def test_movement_records_before_and_after(self, stock):
        movement = self._movement(stock)
        assert movement.on_hand_after - movement.on_hand_before == movement.delta

    def test_stock_item_is_protected_from_deletion_by_the_ledger(self, stock):
        self._movement(stock)
        from django.db.models import ProtectedError

        with pytest.raises(ProtectedError):
            stock.delete()
