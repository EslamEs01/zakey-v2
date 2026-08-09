"""Release reservations whose hold has expired (T-0605, FR-024).

A reservation is a promise that stock is set aside for someone. It has to
expire, or an abandoned basket removes an item from sale permanently — the shop
sells out without selling anything.

The sweep is **time-based and owner-blind**: any ACTIVE reservation past its
``expires_at`` is released, whoever placed it. That is deliberate and is what
separates this from ``reset_dev_state``, which is scoped to automated-QA orders
and refuses to run outside development. This one is safe in production because
expiry is a rule the customer already agreed to, not an administrative override.

Idempotent by construction: the second run finds nothing still expired, because
the first run moved those rows out of ACTIVE. Batched so a long-neglected
database does not lock the whole table in one transaction.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Release stock reservations whose expiry has passed (idempotent, batched)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=500,
            help="Rows locked per transaction. Lower it on a contended database.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many would be released without releasing them.",
        )
        parser.add_argument("--json", action="store_true", help="Machine-readable output.")

    def handle(self, *args, **options):
        from django.utils import timezone

        from apps.inventory import services as inventory_services
        from apps.inventory.models import ReservationState, StockReservation

        if options.get("dry_run"):
            pending = StockReservation.objects.filter(
                state=ReservationState.ACTIVE, expires_at__lt=timezone.now()
            ).count()
            self._emit(options, {"released": 0, "pending": pending, "dry_run": True})
            return

        released = inventory_services.release_expired(
            batch_size=options.get("batch_size", 500)
        )
        remaining = StockReservation.objects.filter(
            state=ReservationState.ACTIVE, expires_at__lt=timezone.now()
        ).count()
        self._emit(options, {"released": released, "pending": remaining, "dry_run": False})

    def _emit(self, options, payload: dict) -> None:
        if options.get("json"):
            self.stdout.write(json.dumps(payload))
            return
        if payload["dry_run"]:
            self.stdout.write(f"would release {payload['pending']} expired reservation(s)")
            return
        self.stdout.write(
            self.style.SUCCESS(f"released {payload['released']} expired reservation(s)")
        )
        if payload["pending"]:
            # Should be zero; a non-zero value means rows expired mid-sweep.
            self.stdout.write(f"  {payload['pending']} still pending — re-run to clear")
