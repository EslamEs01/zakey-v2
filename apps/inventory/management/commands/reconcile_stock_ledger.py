"""Record audited explanations for ledger discontinuities (FR-021, T-0606).

``verify_stock_integrity`` reports a ``ledger_chain`` break when two adjacent
movements disagree about the balance between them. That means something changed
stock without writing a movement. The movement ledger is append-only, so the
break itself is permanent — it is what happened.

This command does not repair the ledger. It records, against a specific gap,
that a named operator examined it and why it is accounted for. After that,
``verify_stock_integrity`` stops reporting **that** gap and keeps reporting
every other one.

Safe in production by design: it writes only an explanation, never a balance,
and it demands a written reason. It is dry-run by default, because an
explanation nobody meant to give is worse than an open alarm.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


class Command(BaseCommand):
    help = "Record an audited explanation for each unreconciled stock-ledger break."

    def add_arguments(self, parser):
        parser.add_argument("--sku", help="Limit to one variant SKU.")
        parser.add_argument(
            "--reason",
            help="Operator-visible explanation. Required to write anything.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Actually record the explanations. Without this, reports only.",
        )
        parser.add_argument("--json", action="store_true", help="Machine-readable output.")

    def handle(self, *args, **options):
        from apps.inventory import services
        from apps.inventory.models import StockItem, StockMovement

        sku = options.get("sku")
        breaks = services.unreconciled_ledger_breaks(sku=sku)

        if not breaks:
            self._emit(options, {"unreconciled": 0, "recorded": 0}, "No unreconciled ledger breaks.")
            return

        if not options.get("apply"):
            self._emit(
                options,
                {"unreconciled": len(breaks), "recorded": 0},
                f"{len(breaks)} unreconciled ledger break(s). "
                "Re-run with --apply and --reason to record an explanation.",
                breaks,
            )
            return

        reason = (options.get("reason") or "").strip()
        if not reason:
            raise CommandError(
                "--reason is required with --apply. An unexplained reconciliation "
                "is indistinguishable from concealing the problem."
            )

        recorded = 0
        with transaction.atomic():
            for drift in breaks:
                note = drift.get("note", "")
                # "<field> breaks between movement <a> and <b>"
                parts = note.split()
                if len(parts) < 7:
                    raise CommandError(f"cannot parse ledger break: {note!r}")
                field = parts[0]
                from_id, to_id = int(parts[-3]), int(parts[-1])

                item = StockItem.objects.select_related("variant").get(
                    variant__sku=drift["sku"]
                )
                services.reconcile_ledger_break(
                    stock_item=item,
                    field=field,
                    from_movement=StockMovement.objects.get(pk=from_id),
                    to_movement=StockMovement.objects.get(pk=to_id),
                    reason=reason,
                )
                recorded += 1

        remaining = len(services.unreconciled_ledger_breaks(sku=sku))
        self._emit(
            options,
            {"unreconciled": len(breaks), "recorded": recorded, "remaining": remaining},
            f"recorded {recorded} reconciliation(s); {remaining} break(s) remain",
        )

    def _emit(self, options, payload: dict, message: str, breaks=None) -> None:
        if options.get("json"):
            if breaks is not None:
                payload["breaks"] = breaks
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        self.stdout.write(message)
        for drift in breaks or []:
            self.stdout.write(f"  {drift['sku']}: {drift['note']} "
                              f"(stored={drift['stored']} derived={drift['derived']})")
