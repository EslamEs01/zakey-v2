"""Report payment/order divergence (T-1106, FR-076).

Reports. Never repairs. A reconciliation tool that silently fixes what it finds
destroys the evidence of the bug that caused the divergence, and the next
divergence looks like the first.

Exits non-zero when anything diverges so a scheduled run fails loudly instead of
scrolling past in a log.
"""

from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.payments.services import reconcile


class Command(BaseCommand):
    help = "Report divergence between the payment ledger and order payment status."

    def add_arguments(self, parser):
        parser.add_argument(
            "--order",
            dest="order_number",
            help="Reconcile a single order by number instead of all of them.",
        )
        parser.add_argument(
            "--json",
            action="store_true",
            help="Emit machine-readable output for a monitoring pipeline.",
        )

    def handle(self, *args, **options):
        target = None
        if options.get("order_number"):
            from apps.orders.models import Order

            target = Order.objects.filter(number=options["order_number"]).first()
            if target is None:
                raise CommandError(f"No order numbered {options['order_number']!r}.")

        divergences = reconcile(target)

        if options.get("json"):
            self.stdout.write(json.dumps(divergences, ensure_ascii=False, indent=2))
        elif not divergences:
            self.stdout.write(self.style.SUCCESS("No divergence found."))
        else:
            self.stdout.write(self.style.ERROR(f"{len(divergences)} divergence(s):"))
            for item in divergences:
                note = f" — {item['note']}" if item.get("note") else ""
                self.stdout.write(
                    f"  {item['order']}: {item['field']} "
                    f"stored={item['stored']} derived={item['derived']}{note}"
                )

        if divergences:
            # Non-zero exit: this is the signal a scheduler acts on.
            raise CommandError(f"{len(divergences)} payment divergence(s) found.")
