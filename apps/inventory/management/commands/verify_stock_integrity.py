"""Report inventory drift (T-0606, FR-027, FR-021).

Reports. Never repairs. A stock tool that silently fixes what it finds destroys
the evidence of the bug that caused the drift, and the next drift then looks
like the first.

Exits non-zero when anything has drifted, so a scheduled run fails loudly
instead of scrolling past in a log. Low stock is a commercial fact rather than a
data defect, so it is reported but never fails the command.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.inventory.services import low_stock_report, verify_stock_integrity


class Command(BaseCommand):
    help = "Report drift between the stock ledger, reservations and stored balances."

    def add_arguments(self, parser):
        parser.add_argument(
            "--sku",
            dest="sku",
            help="Verify a single variant by SKU instead of the whole catalogue.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emit machine-readable output for a monitoring pipeline.",
        )
        parser.add_argument(
            "--low-stock",
            action="store_true",
            help="Also list items at or below their low-stock threshold (FR-027).",
        )

    def handle(self, *args, **options):
        sku = options.get("sku")
        if sku:
            from apps.inventory.models import StockItem

            if not StockItem.objects.filter(variant__sku=sku).exists():
                raise CommandError(f"No stock item for SKU {sku!r}.")

        drifts = verify_stock_integrity(sku=sku)
        low = low_stock_report(sku=sku) if options.get("low_stock") else []

        if options.get("json"):
            payload = {"drift": drifts}
            if options.get("low_stock"):
                payload["low_stock"] = low
            self.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            if not drifts:
                self.stdout.write(self.style.SUCCESS("No stock drift found."))
            else:
                self.stdout.write(self.style.ERROR(f"{len(drifts)} drift(s):"))
                for item in drifts:
                    note = f" — {item['note']}" if item.get("note") else ""
                    self.stdout.write(
                        f"  {item['sku']}: {item['check']} "
                        f"stored={item['stored']} derived={item['derived']}{note}"
                    )
            if options.get("low_stock"):
                if not low:
                    self.stdout.write("No item is below its low-stock threshold.")
                else:
                    self.stdout.write(f"{len(low)} item(s) at or below threshold:")
                    for entry in low:
                        self.stdout.write(
                            f"  {entry['sku']}: available={entry['available']} "
                            f"threshold={entry['threshold']} ({entry['state']})"
                        )

        if drifts:
            # Non-zero exit: this is the signal a scheduler acts on. Low stock
            # deliberately does not reach here.
            raise CommandError(f"{len(drifts)} stock drift(s) found.")
