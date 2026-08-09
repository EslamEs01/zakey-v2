"""Data retention (T-1708, threat T-13, NFR-012).

Two opposite failures are both unacceptable here, so both are tested:

* keeping personal data forever, which is the liability the policy exists to
  shed;
* deleting financial history, which is the record the business is legally
  obliged to keep.

The command is dry-run by default. That is the single most important property in
this file: a retention job that deletes on its first accidental invocation is a
data-loss incident waiting for a cron typo.
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

pytestmark = pytest.mark.django_db


def run(*args) -> str:
    out = StringIO()
    call_command("purge_expired_data", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def age(queryset, **field_deltas) -> None:
    """Backdate rows past a retention window, bypassing auto_now."""
    queryset.update(**field_deltas)


@pytest.fixture
def old_contact_message(db):
    from apps.content.models import ContactMessage

    message = ContactMessage.objects.create(
        name="ندى",
        email="nada@example.com",
        phone="01012345678",
        subject="استفسار",
        message="رسالة طويلة بما يكفي لتجاوز الحد الأدنى المطلوب للرسائل.",
    )
    age(
        ContactMessage.objects.filter(pk=message.pk),
        created_at=timezone.now() - timedelta(days=400),
    )
    return message


@pytest.fixture
def old_order(db):
    from apps.orders.models import Order

    order = Order.objects.create(
        number="ZK-OLD-1",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="key-old-1",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )
    age(
        Order.objects.filter(pk=order.pk),
        created_at=timezone.now() - timedelta(days=4000),
    )
    return order


# ---------------------------------------------------------------------------
# Dry run is the default
# ---------------------------------------------------------------------------


class TestDryRunIsTheDefault:
    def test_running_with_no_flags_deletes_nothing(self, old_contact_message):
        from apps.content.models import ContactMessage

        output = run()

        assert ContactMessage.objects.filter(pk=old_contact_message.pk).exists()
        assert "Would delete" in output
        assert "Dry run" in output

    def test_the_dry_run_still_reports_what_it_would_remove(self, old_contact_message):
        payload = json.loads(run("--json"))

        assert payload["applied"] is False
        assert payload["counts"]["contact_messages"] == 1

    def test_apply_actually_deletes(self, old_contact_message):
        from apps.content.models import ContactMessage

        output = run("--apply")

        assert not ContactMessage.objects.filter(pk=old_contact_message.pk).exists()
        assert "Deleted" in output


# ---------------------------------------------------------------------------
# What gets removed
# ---------------------------------------------------------------------------


class TestExpiredDataIsRemoved:
    def test_an_abandoned_anonymous_cart_is_removed(self, db, variant):
        from apps.cart.models import Cart, CartStatus

        cart = Cart.objects.create(session_key="abandoned-key", status=CartStatus.ACTIVE)
        age(
            Cart.objects.filter(pk=cart.pk),
            updated_at=timezone.now() - timedelta(days=200),
        )

        run("--apply")

        assert not Cart.objects.filter(pk=cart.pk).exists()

    def test_a_recent_cart_survives(self, db):
        from apps.cart.models import Cart, CartStatus

        cart = Cart.objects.create(session_key="fresh-key", status=CartStatus.ACTIVE)

        run("--apply")

        assert Cart.objects.filter(pk=cart.pk).exists()

    def test_a_converted_cart_survives_regardless_of_age(self, db):
        """A converted cart is the provenance of an order."""
        from apps.cart.models import Cart, CartStatus

        cart = Cart.objects.create(session_key="converted", status=CartStatus.CONVERTED)
        age(
            Cart.objects.filter(pk=cart.pk),
            updated_at=timezone.now() - timedelta(days=900),
        )

        run("--apply")

        assert Cart.objects.filter(pk=cart.pk).exists()

    def test_an_unconfirmed_subscription_is_removed(self, db):
        from apps.content.models import NewsletterSubscription

        sub = NewsletterSubscription.objects.create(
            email="ghost@example.com", confirmed=False
        )
        age(
            NewsletterSubscription.objects.filter(pk=sub.pk),
            created_at=timezone.now() - timedelta(days=90),
        )

        run("--apply")

        assert not NewsletterSubscription.objects.filter(pk=sub.pk).exists()

    def test_a_confirmed_subscription_survives(self, db):
        from apps.content.models import NewsletterSubscription

        sub = NewsletterSubscription.objects.create(
            email="real@example.com", confirmed=True
        )
        age(
            NewsletterSubscription.objects.filter(pk=sub.pk),
            created_at=timezone.now() - timedelta(days=900),
        )

        run("--apply")

        assert NewsletterSubscription.objects.filter(pk=sub.pk).exists()


# ---------------------------------------------------------------------------
# What must never be removed — the load-bearing half
# ---------------------------------------------------------------------------


class TestFinancialHistoryIsNeverDeleted:
    def test_an_ancient_order_survives(self, old_order):
        from apps.orders.models import Order

        run("--apply")

        assert Order.objects.filter(pk=old_order.pk).exists(), (
            "retention deleted financial history"
        )

    def test_order_lines_survive(self, old_order, variant):
        from apps.orders.models import OrderLine

        line = OrderLine.objects.create(
            order=old_order,
            variant=variant,
            product_name=variant.product.name,
            sku=variant.sku,
            unit_price=variant.price,
            quantity=1,
            line_total=variant.price,
        )

        run("--apply")

        assert OrderLine.objects.filter(pk=line.pk).exists()

    def test_the_audit_log_survives(self, db):
        from apps.audit.models import AuditAction, AuditLog
        from apps.audit.services import record_audit
        from apps.content.models import NewsletterSubscription

        subject = NewsletterSubscription.objects.create(email="audited@example.com")
        entry = record_audit(None, AuditAction.UPDATE, subject, {})
        age(
            AuditLog.objects.filter(pk=entry.pk),
            created_at=timezone.now() - timedelta(days=4000),
        )

        run("--apply")

        assert AuditLog.objects.filter(pk=entry.pk).exists(), (
            "retention deleted the audit trail"
        )

    def test_stock_movements_survive(self, variant, stock):
        from apps.inventory import services as inventory_services
        from apps.inventory.models import StockMovement

        inventory_services.adjust(variant, 3, "purchase")
        pks = list(StockMovement.objects.values_list("pk", flat=True))
        age(
            StockMovement.objects.filter(pk__in=pks),
            created_at=timezone.now() - timedelta(days=4000),
        )

        run("--apply")

        assert StockMovement.objects.filter(pk__in=pks).count() == len(pks)

    def test_the_command_states_what_it_retains(self, db):
        output = run()

        assert "retained by design" in output


# ---------------------------------------------------------------------------
# Idempotence
# ---------------------------------------------------------------------------


def test_running_twice_removes_nothing_the_second_time(old_contact_message):
    first = json.loads(run("--apply", "--json"))
    second = json.loads(run("--apply", "--json"))

    assert first["counts"]["contact_messages"] == 1
    assert second["counts"]["contact_messages"] == 0
