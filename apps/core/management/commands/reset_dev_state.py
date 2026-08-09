"""Release stock held by automated browser-QA orders (development only).

The browser suites place **real orders**, and a real order holds a real stock
reservation until it is fulfilled, cancelled, or expires. Nothing in a
development environment ever does those things, so every ``npm run qa`` leaves
the flagship variant slightly more reserved than it found it. After enough runs
``available`` reaches zero and checkout starts refusing — correctly. The shop
really had sold out. A gate that only passes on a fresh database is not a gate.

**Scope is the whole design.** An earlier version of this command released every
active reservation, which would also have released a developer's own
half-finished basket. It now touches only reservations whose order was placed by
the automated suite, identified by the email domain the suite exclusively owns:

    QA_EMAIL_DOMAIN = "e2e.zakey.invalid"

``.invalid`` is reserved by RFC 2606 and can never resolve, so no real customer
can ever hold an address in it. That makes the marker unambiguous rather than
heuristic — unlike ``@example.com``, which a developer testing by hand would
plausibly type.

What it does **not** do:

* it does not delete orders, order lines, payments, refunds or audit rows —
  history stays intact and the ledger keeps reconciling;
* it does not edit ``on_hand``; stock levels are only ever moved by the
  inventory service, through the movement ledger;
* it has no ``--force``, no production override, and no way to widen its scope
  from the command line.
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

#: The suite's own domain. RFC 2606 reserved: never a real customer.
QA_EMAIL_DOMAIN = "e2e.zakey.invalid"


class Command(BaseCommand):
    help = (
        "Release stock reservations held by automated browser-QA orders so the "
        "QA gate is repeatable. Development only; never touches real data."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would be released without changing anything.",
        )

    def handle(self, *args, **options):
        self._guard_environment()

        from apps.inventory.models import ReservationState, StockItem, StockReservation

        dry_run = options.get("dry_run", False)

        if not dry_run:
            self._apply_pending_migrations()

        # Only reservations belonging to an order the automated suite placed.
        # A reservation with no order (a bare basket hold) is never QA-owned by
        # this definition, so it is left alone.
        candidates = StockReservation.objects.filter(
            state=ReservationState.ACTIVE,
            order__isnull=False,
            order__email__iendswith=f"@{QA_EMAIL_DOMAIN}",
        )

        if dry_run:
            count = candidates.count()
            self.stdout.write(f"would release {count} QA reservation(s)")
            self._report_availability()
            return

        from apps.inventory import services as inventory_services

        released = 0
        # One transaction: a partial release would leave `reserved` disagreeing
        # with the sum of active reservations, which is exactly the drift
        # `verify_stock_integrity` exists to catch.
        #
        # The release goes through the inventory *service*, not through a direct
        # write to `StockItem.reserved`. An earlier version edited the column by
        # hand and left no movement row, so the ledger head stopped matching the
        # stored balance — the integrity command caught it immediately. Stock
        # moves one way only, through the ledger (FR-021).
        with transaction.atomic():
            pks = list(
                candidates.order_by("stock_item_id", "pk").values_list("pk", flat=True)
            )
            for pk in pks:  # deterministic order: lowest stock_item first
                reservation = StockReservation.objects.select_for_update().get(pk=pk)
                if reservation.state != ReservationState.ACTIVE:
                    continue  # re-checked inside the lock; makes reruns safe
                # `expired=False`: an expiry is time-driven, this is a
                # deliberate administrative release, so RELEASED is the
                # truthful state to record.
                inventory_services.release(reservation)
                released += 1

        self.stdout.write(f"released {released} QA reservation(s)")
        self._report_availability()

    # -- guards -----------------------------------------------------------
    def _apply_pending_migrations(self) -> None:
        """Bring the development schema up to the code before anything reads it.

        `npm run qa` calls this command and then drives a live server with
        Playwright. If a migration has been written but not applied, the schema
        lags the code and the first query touching a new column raises a 500 —
        which surfaces as a failing end-to-end journey with no obvious link to
        the real cause. That is exactly how an unapplied
        `shipping.0002_launch_free_threshold_only` cost a QA run: eight checkout
        journeys failed on `column ... does not exist`.

        Safe every time: `migrate` is a no-op when nothing is pending, and
        `_guard_environment` has already refused to run outside development.
        """
        from io import StringIO

        from django.core.management import call_command

        buffer = StringIO()
        call_command("migrate", "--noinput", stdout=buffer, verbosity=1)
        applied = [
            line.strip()
            for line in buffer.getvalue().splitlines()
            if line.strip().startswith("Applying")
        ]
        if applied:
            self.stdout.write(f"applied {len(applied)} pending migration(s):")
            for line in applied:
                self.stdout.write(f"  {line}")

    def _guard_environment(self) -> None:
        """Refuse anything that could plausibly be production."""
        if not settings.DEBUG:
            raise CommandError(
                "reset_dev_state refuses to run with DEBUG=False. It releases "
                "stock reservations, which outside development would return "
                "held stock to the shelf underneath real customers."
            )
        # DEBUG alone is not proof: a misconfigured production box can have it
        # on, which is precisely when this command would do the most damage.
        for name in ("SECURE_SSL_REDIRECT", "SESSION_COOKIE_SECURE"):
            if getattr(settings, name, False):
                raise CommandError(
                    f"reset_dev_state refuses to run: {name} is enabled, which "
                    "indicates a production-like configuration."
                )
        if not settings.ALLOWED_HOSTS or set(settings.ALLOWED_HOSTS) - {
            "localhost",
            "127.0.0.1",
            "testserver",
            "[::1]",
            "*",
        }:
            raise CommandError(
                "reset_dev_state refuses to run: ALLOWED_HOSTS names a real "
                f"host ({settings.ALLOWED_HOSTS}), indicating a deployed site."
            )

    def _report_availability(self) -> None:
        """Bounded, non-sensitive summary. No customer data is printed."""
        from apps.inventory.models import StockItem

        items = list(StockItem.objects.select_related("variant"))
        unavailable = [item for item in items if item.available <= 0]
        self.stdout.write(
            f"{len(items) - len(unavailable)} of {len(items)} variants have availability"
        )
        if unavailable:
            # SKUs are catalogue identifiers, not personal data.
            self.stdout.write(
                "  no availability: "
                + ", ".join(sorted(i.variant.sku for i in unavailable)[:10])
            )
