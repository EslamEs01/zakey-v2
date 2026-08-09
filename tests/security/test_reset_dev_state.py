"""Safety of the QA state-reset command (T-1801 repeatability, FR-029, INV-001).

This command exists so the browser gate is repeatable. It releases stock held by
automated-QA orders, which is a *write to inventory* — so the interesting tests
are not the ones proving it works, but the ones proving how narrowly it works.

The failure it must never cause: releasing a real reservation, handing stock
that someone is holding back to the shelf underneath them.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from apps.core.management.commands.reset_dev_state import QA_EMAIL_DOMAIN
from apps.inventory import services as inventory_services
from apps.inventory.models import ReservationState, StockItem, StockReservation
from apps.orders.models import Order

pytestmark = pytest.mark.django_db


def run(*args) -> str:
    out = StringIO()
    call_command("reset_dev_state", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


@pytest.fixture
def dev_env(settings):
    """A configuration the command considers safely non-production."""
    settings.DEBUG = True
    settings.SECURE_SSL_REDIRECT = False
    settings.SESSION_COOKIE_SECURE = False
    settings.ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]
    return settings


def make_order(email: str, number: str) -> Order:
    return Order.objects.create(
        number=number,
        email=email,
        phone="01012345678",
        idempotency_key=f"key-{number}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
        placed_at=timezone.now(),
    )


def reserve_for(order, variant, quantity=2) -> StockReservation:
    reservation = inventory_services.reserve(variant, quantity, order=order)
    return reservation


# ---------------------------------------------------------------------------
# 1. Unsafe configurations are refused
# ---------------------------------------------------------------------------


class TestEnvironmentGuards:
    def test_debug_false_is_refused(self, settings, stock):
        settings.DEBUG = False

        with pytest.raises(CommandError) as caught:
            run()

        assert "DEBUG=False" in str(caught.value)

    def test_a_production_like_ssl_setting_is_refused(self, dev_env, stock):
        """DEBUG alone is not proof — a misconfigured box can have it on."""
        dev_env.SECURE_SSL_REDIRECT = True

        with pytest.raises(CommandError) as caught:
            run()

        assert "production-like" in str(caught.value)

    def test_a_secure_cookie_setting_is_refused(self, dev_env, stock):
        dev_env.SESSION_COOKIE_SECURE = True

        with pytest.raises(CommandError):
            run()

    def test_a_real_allowed_host_is_refused(self, dev_env, stock):
        dev_env.ALLOWED_HOSTS = ["zakey.example.eg"]

        with pytest.raises(CommandError) as caught:
            run()

        assert "deployed site" in str(caught.value)

    def test_a_refused_run_changes_nothing(self, settings, variant, stock):
        order = make_order(f"buyer@{QA_EMAIL_DOMAIN}", "ZK-QA-1")
        reserve_for(order, variant)
        settings.DEBUG = False
        before = StockItem.objects.get(pk=stock.pk).reserved

        with pytest.raises(CommandError):
            run()

        assert StockItem.objects.get(pk=stock.pk).reserved == before

    def test_there_is_no_force_or_production_override(self):
        """A bypass flag would defeat every guard above."""
        from apps.core.management.commands.reset_dev_state import Command

        parser = Command().create_parser("manage.py", "reset_dev_state")
        options = {action.dest for action in parser._actions}

        assert "force" not in options
        assert not {o for o in options if "prod" in o or "yes" in o}


# ---------------------------------------------------------------------------
# 2 & 3. It releases QA holds and nothing else
# ---------------------------------------------------------------------------


class TestScope:
    def test_a_qa_reservation_is_released(self, dev_env, variant, stock):
        order = make_order(f"buyer@{QA_EMAIL_DOMAIN}", "ZK-QA-1")
        reserve_for(order, variant, 2)
        assert StockItem.objects.get(pk=stock.pk).reserved == 2

        run()

        assert StockItem.objects.get(pk=stock.pk).reserved == 0
        assert (
            StockReservation.objects.get(order=order).state == ReservationState.RELEASED
        )

    def test_a_real_customers_reservation_is_untouched(self, dev_env, variant, stock):
        """The load-bearing test: real held stock must stay held."""
        real = make_order("nada@example.com", "ZK-REAL-1")
        reserve_for(real, variant, 3)

        run()

        assert StockItem.objects.get(pk=stock.pk).reserved == 3
        assert StockReservation.objects.get(order=real).state == ReservationState.ACTIVE

    def test_a_developer_using_example_com_is_untouched(self, dev_env, variant, stock):
        """`@example.com` is NOT the marker — a developer types it by hand."""
        dev = make_order("dev@example.com", "ZK-DEV-1")
        reserve_for(dev, variant, 1)

        run()

        assert StockReservation.objects.get(order=dev).state == ReservationState.ACTIVE

    def test_a_basket_hold_with_no_order_is_untouched(self, dev_env, variant, stock):
        """A bare cart hold has no order, so it can never be QA-owned."""
        reservation = inventory_services.reserve(variant, 2)

        run()

        reservation.refresh_from_db()
        assert reservation.state == ReservationState.ACTIVE
        assert StockItem.objects.get(pk=stock.pk).reserved == 2

    def test_mixed_state_releases_only_the_qa_share(self, dev_env, variant, stock):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-2")
        real = make_order("omar@example.com", "ZK-REAL-2")
        reserve_for(qa, variant, 4)
        reserve_for(real, variant, 3)
        assert StockItem.objects.get(pk=stock.pk).reserved == 7

        run()

        assert StockItem.objects.get(pk=stock.pk).reserved == 3
        assert StockReservation.objects.get(order=real).state == ReservationState.ACTIVE
        assert StockReservation.objects.get(order=qa).state == ReservationState.RELEASED

    def test_an_already_released_reservation_is_not_double_counted(
        self, dev_env, variant, stock
    ):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-3")
        reservation = reserve_for(qa, variant, 2)
        inventory_services.release(reservation)

        run()

        assert StockItem.objects.get(pk=stock.pk).reserved == 0


# ---------------------------------------------------------------------------
# 4 & 5. Invariants and history survive
# ---------------------------------------------------------------------------


class TestIntegrity:
    def test_inventory_invariants_hold_afterwards(self, dev_env, variant, stock):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-4")
        reserve_for(qa, variant, 5)

        run()

        item = StockItem.objects.get(pk=stock.pk)
        assert item.reserved >= 0
        assert item.reserved <= item.on_hand
        assert item.available == item.on_hand - item.reserved

    def test_the_stock_ledger_still_reconciles(self, dev_env, variant, stock):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-5")
        reserve_for(qa, variant, 3)

        run()

        drifts = inventory_services.verify_stock_integrity()
        assert drifts == [], f"the reset left the ledger inconsistent: {drifts}"

    def test_orders_are_never_deleted_or_altered(self, dev_env, variant, stock):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-6")
        reserve_for(qa, variant, 2)
        before = Order.objects.get(pk=qa.pk)
        snapshot = (before.number, before.status, before.grand_total, before.email)

        run()

        after = Order.objects.get(pk=qa.pk)
        assert (after.number, after.status, after.grand_total, after.email) == snapshot

    def test_on_hand_is_never_edited(self, dev_env, variant, stock):
        """Stock levels move only through the ledger (FR-021)."""
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-7")
        reserve_for(qa, variant, 2)
        before = StockItem.objects.get(pk=stock.pk).on_hand

        run()

        assert StockItem.objects.get(pk=stock.pk).on_hand == before

    def test_the_audit_log_is_not_purged(self, dev_env, variant, stock):
        from apps.audit.models import AuditLog

        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-8")
        reserve_for(qa, variant, 2)
        before = AuditLog.objects.count()

        run()

        assert AuditLog.objects.count() >= before


# ---------------------------------------------------------------------------
# 6, 7, 8, 9. Idempotence, atomicity, determinism
# ---------------------------------------------------------------------------


class TestRepeatability:
    def test_running_twice_is_idempotent(self, dev_env, variant, stock):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-9")
        reserve_for(qa, variant, 3)

        first = run()
        after_first = StockItem.objects.get(pk=stock.pk).reserved
        second = run()
        after_second = StockItem.objects.get(pk=stock.pk).reserved

        assert "released 1 QA reservation(s)" in first
        assert "released 0 QA reservation(s)" in second
        assert after_first == after_second == 0

    def test_availability_is_deterministic_across_simulated_runs(
        self, dev_env, variant, stock
    ):
        """The flagship variant must not lose availability run after run."""
        baseline = StockItem.objects.get(pk=stock.pk).available
        observed = []

        for index in range(4):
            order = make_order(f"bot{index}@{QA_EMAIL_DOMAIN}", f"ZK-LOOP-{index}")
            reserve_for(order, variant, 2)
            run()
            observed.append(StockItem.objects.get(pk=stock.pk).available)

        assert observed == [baseline] * 4, (
            f"availability drifted across runs: {observed} (baseline {baseline})"
        )

    def test_a_failure_rolls_back_atomically(self, dev_env, variant, stock, monkeypatch):
        """A half-applied release would desynchronise `reserved` from the rows."""
        first = make_order(f"a@{QA_EMAIL_DOMAIN}", "ZK-ATOM-1")
        second = make_order(f"b@{QA_EMAIL_DOMAIN}", "ZK-ATOM-2")
        reserve_for(first, variant, 2)
        reserve_for(second, variant, 2)
        before = StockItem.objects.get(pk=stock.pk).reserved
        assert before == 4

        calls = {"n": 0}
        original = StockReservation.save

        def explode(self, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] > 1:
                raise RuntimeError("simulated failure mid-release")
            return original(self, *args, **kwargs)

        monkeypatch.setattr(StockReservation, "save", explode)

        with pytest.raises(RuntimeError):
            run()

        assert StockItem.objects.get(pk=stock.pk).reserved == before, (
            "a partial release survived the rollback"
        )
        assert (
            StockReservation.objects.filter(state=ReservationState.ACTIVE).count() == 2
        )

    def test_dry_run_changes_nothing(self, dev_env, variant, stock):
        qa = make_order(f"bot@{QA_EMAIL_DOMAIN}", "ZK-QA-10")
        reserve_for(qa, variant, 2)

        output = run("--dry-run")

        assert "would release 1" in output
        assert StockItem.objects.get(pk=stock.pk).reserved == 2

    def test_the_report_leaks_no_personal_data(self, dev_env, variant, stock):
        qa = make_order(f"secret-person@{QA_EMAIL_DOMAIN}", "ZK-QA-11")
        reserve_for(qa, variant, 2)

        output = run()

        assert "secret-person" not in output
        assert QA_EMAIL_DOMAIN not in output


# ---------------------------------------------------------------------------
# The marker itself
# ---------------------------------------------------------------------------


class TestTheMarker:
    def test_the_domain_is_reserved_and_cannot_be_a_real_customer(self):
        """RFC 2606 reserves `.invalid`; it can never resolve."""
        assert QA_EMAIL_DOMAIN.endswith(".invalid")

    def test_the_browser_suite_uses_the_marker(self):
        """If the specs drift back to @example.com the cleanup silently stops."""
        from pathlib import Path

        from django.conf import settings

        offenders = []
        for spec in Path(settings.BASE_DIR, "tests").rglob("*.spec.js"):
            text = spec.read_text(encoding="utf-8")
            if "@example.com" in text:
                offenders.append(str(spec.relative_to(settings.BASE_DIR)))

        assert offenders == [], (
            "browser specs create orders outside the QA domain, so "
            f"reset_dev_state cannot clean them up: {offenders}"
        )
