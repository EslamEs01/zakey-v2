"""Expire abandoned carts after their TTL (T-0708, FR-038).

`tasks.md` names this command and it did not exist. A cart that never expires
keeps its reservations, and a reservation that never expires removes stock from
sale permanently — the shop sells out without selling anything.

Idempotent: the second run finds nothing still active past its TTL, because the
first moved those carts out of ACTIVE. Batched so a long-neglected database does
not lock the whole table at once.
"""

from __future__ import annotations

import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


class Command(BaseCommand):
    help = "Mark carts abandoned once they pass the configured TTL (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--json", action="store_true")

    def handle(self, *args, **options):
        from apps.cart.models import Cart, CartStatus
        from apps.core.models import SiteSetting

        ttl_days = SiteSetting.objects.get_solo().cart_ttl_days
        cutoff = timezone.now() - timedelta(days=ttl_days)
        stale = Cart.objects.filter(status=CartStatus.ACTIVE, updated_at__lt=cutoff)

        if options.get("dry_run"):
            self._emit(options, {"expired": 0, "pending": stale.count(), "ttl_days": ttl_days})
            return

        expired = 0
        batch_size = options.get("batch_size") or 500
        while True:
            pks = list(stale.values_list("pk", flat=True)[:batch_size])
            if not pks:
                break
            with transaction.atomic():
                # `updated_at` is auto_now, so the status change is applied with
                # `update()` — otherwise every save would refresh the timestamp
                # and the cart would never look stale again.
                expired += Cart.objects.filter(pk__in=pks).update(
                    status=CartStatus.ABANDONED
                )

        self._emit(
            options,
            {"expired": expired, "pending": stale.count(), "ttl_days": ttl_days},
        )

    def _emit(self, options, payload: dict) -> None:
        if options.get("json"):
            self.stdout.write(json.dumps(payload))
            return
        verb = "would expire" if options.get("dry_run") else "expired"
        count = payload["pending"] if options.get("dry_run") else payload["expired"]
        self.stdout.write(
            f"{verb} {count} cart(s) older than {payload['ttl_days']} day(s)"
        )
