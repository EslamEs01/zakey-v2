"""Data retention, as a command (T-1708, threat T-13, NFR-012).

Keeping personal data forever is a liability that grows on its own. This is the
one sanctioned way to shed it.

Three rules shape what it will and will not touch:

* **Dry run by default.** Deletion is irreversible, so the destructive path is
  opt-in via ``--apply``. A retention job that deletes on its first accidental
  invocation is a data-loss incident waiting for a cron typo.
* **Financial history is never deleted.** Orders, payments, refunds and the
  audit log are retained regardless of age: they are the record of what the
  business did, and Egyptian bookkeeping obligations outlive any privacy
  window. Where a *person* must be forgotten, the order is anonymised in place
  rather than removed, so the totals still reconcile.
* **Append-only ledgers stay append-only.** ``StockMovement``, ``PaymentEvent``,
  ``OrderEvent`` and ``AuditLog`` refuse deletion at the model level, and this
  command does not try to work around that.
"""

from __future__ import annotations

import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

#: Anonymous baskets nobody came back to.
ABANDONED_CART_DAYS = 90

#: A handled enquiry stops being useful long before it stops being personal.
CONTACT_MESSAGE_DAYS = 365

#: An address someone never confirmed.
UNCONFIRMED_SUBSCRIPTION_DAYS = 30

#: Reservations already released; the row is only of forensic interest briefly.
DEAD_RESERVATION_DAYS = 30


class Command(BaseCommand):
    help = "Apply the data-retention policy. Reports by default; deletes only with --apply."

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually delete. Without this the command only reports.",
        )
        parser.add_argument(
            "--json", action="store_true", help="Machine-readable output."
        )

    def handle(self, *args, **options):
        apply_changes = options.get("apply", False)
        now = timezone.now()
        report: dict[str, int] = {}

        from apps.cart.models import Cart, CartStatus
        from apps.content.models import ContactMessage, NewsletterSubscription
        from apps.inventory.models import ReservationState, StockReservation

        targets = [
            (
                "abandoned_carts",
                Cart.objects.filter(
                    updated_at__lt=now - timedelta(days=ABANDONED_CART_DAYS),
                    customer__isnull=True,
                ).exclude(status=CartStatus.CONVERTED),
            ),
            (
                "contact_messages",
                ContactMessage.objects.filter(
                    created_at__lt=now - timedelta(days=CONTACT_MESSAGE_DAYS)
                ),
            ),
            (
                "unconfirmed_subscriptions",
                NewsletterSubscription.objects.filter(
                    created_at__lt=now - timedelta(days=UNCONFIRMED_SUBSCRIPTION_DAYS),
                    confirmed=False,
                ),
            ),
            (
                "dead_reservations",
                StockReservation.objects.filter(
                    updated_at__lt=now - timedelta(days=DEAD_RESERVATION_DAYS)
                ).exclude(state=ReservationState.ACTIVE),
            ),
        ]

        for name, queryset in targets:
            count = queryset.count()
            report[name] = count
            if apply_changes and count:
                with transaction.atomic():
                    queryset.delete()

        if options.get("json"):
            self.stdout.write(
                json.dumps({"applied": apply_changes, "counts": report}, indent=2)
            )
        else:
            verb = "Deleted" if apply_changes else "Would delete"
            for name, count in report.items():
                self.stdout.write(f"  {verb} {count} {name.replace('_', ' ')}")
            if not apply_changes:
                self.stdout.write(
                    self.style.WARNING("\nDry run. Re-run with --apply to delete.")
                )
            else:
                self.stdout.write(self.style.SUCCESS("\nRetention policy applied."))
            self.stdout.write(
                "Orders, payments, refunds and the audit log are retained by design."
            )
