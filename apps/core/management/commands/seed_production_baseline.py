"""Production launch baseline — operational rows only, no demonstration content.

``seed_demo`` imports the whole approved fixture: nine products with unapproved
prices, nine star-rated scenario cards, the "pre-launch demo, no real orders"
banner, and placeholder contact details. None of that may reach a public
storefront, so the deploy path must never call it.

This command imports only the rows the shop needs in order to *work*:

* the site constants (EGP, VAT 14%, free-shipping threshold 1,500);
* the 27 governorates and their service areas;
* the shipping zone/methods and the payment methods;
* the taxonomy — categories and collections — that staff attach real products to;
* navigation, page copy, FAQs and partners, minus every pre-launch claim.

It creates **no product, no review and no demonstration account**. The catalogue
is filled through the admin with approved figures.

Sanitisation happens on a copy of the fixture *before* any row is written, so a
pre-launch string cannot reach the database and then need unwinding. What it
removes is listed in ``_sanitise``; each entry is a statement that would be
false the moment the shop starts taking orders.

Run once at first deploy. Re-running without ``--force`` is a no-op, so a later
redeploy never overwrites copy that staff have since edited in the admin.

    uv run python manage.py seed_production_baseline [--dry-run] [--force]
"""

from __future__ import annotations

import copy
import json

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

#: Copy that describes free shipping as *planned* (مخطط). The threshold policy
#: is in force from the moment the shop opens, so each of these would be false
#: on a live page. Matched as whole strings rather than by substituting the word
#: everywhere: "تغطية تركيب مخططة" and "سياسة الضمان المخططة" are still accurate
#: — installation really is switched off at launch and the warranty policy
#: really is not published yet — and blanket word-replacement would corrupt them.
LAUNCH_TEXT_REPLACEMENTS = {
    "شحن مجاني مخطط للطلبات فوق 1,500 ج.م": "شحن مجاني للطلبات من 1,500 ج.م",
    "حد شحن مجاني مخطط": "حد الشحن المجاني",
    "شحن مجاني مخطط للطلبات المؤهلة عند إطلاق الخدمة.": (
        "شحن مجاني للطلبات المؤهلة من 1,500 ج.م."
    ),
}

#: Both answers state that the storefront cannot take an order or a payment.
#: True of the preview, false the moment cash-on-delivery goes live — and a
#: customer who reads them would reasonably not try to buy. Rewriting them is a
#: content decision for the client, so the launch simply ships without them.
LAUNCH_UNSAFE_FAQ_IDS = frozenset({"faq-unavailable", "faq-payment"})

#: Shown only for a method that is not selectable, so it must describe exactly
#: that and claim nothing about the rest of the shop.
UNAVAILABLE_PAYMENT_NOTICE = "غير متاحة حاليًا."


class Command(BaseCommand):
    help = "Seed the operational launch baseline: no products, no reviews, no prototype notices."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Report what would change; write nothing."
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Reapply even when the baseline is already present. Overwrites staff edits to page copy.",
        )
        parser.add_argument(
            "--actor",
            default="",
            help="Email of the staff member accountable, recorded on the launch-policy audit entry.",
        )

    def handle(self, *args, **options):
        from apps.content.models import HomeSection

        from .seed_demo import FIXTURE, Command as SeedCommand, Report

        dry_run: bool = options["dry_run"]

        if HomeSection.objects.exists() and not options["force"]:
            self.stdout.write(
                self.style.SUCCESS("baseline already applied; nothing to do (--force to reapply)")
            )
            return

        if not FIXTURE.is_file():
            raise CommandError(f"Fixture not found: {FIXTURE}")

        data = self._sanitise(json.loads(FIXTURE.read_text(encoding="utf-8")))

        # The section methods are reused rather than reimplemented: they are the
        # ones the test suite exercises, and a second copy would drift.
        seeder = SeedCommand()
        seeder.dry_run = dry_run
        seeder.verbosity = options.get("verbosity", 1)
        seeder.report = Report()
        seeder.stdout = self.stdout
        seeder.style = self.style

        try:
            with transaction.atomic():
                seeder._seed_settings(data)
                seeder._seed_geography(data)
                seeder._seed_shipping(data)
                seeder._seed_payments(data)
                seeder._seed_categories(data)
                # Empty containers. `_seed_collections` skips product links whose
                # product does not exist, which is every one of them here.
                seeder._seed_collections(data)
                seeder._seed_content(data)
                self._normalise_payment_notices()
                if dry_run:
                    raise _DryRun()
        except _DryRun:
            self.stdout.write(self.style.WARNING("DRY RUN — rolled back, nothing written."))

        seeder._print_report()

        if seeder.report.failed:
            raise CommandError(f"{seeder.report.failed} record(s) failed.")

        # `_seed_shipping` writes rates flagged is_placeholder, which the
        # production system check (zakey.shipping.E001/E002) rejects. Checks run
        # *before* a command does, so `apply_launch_policy` — the command that
        # exists to clear those flags — could not itself be started under
        # production settings once they were written: a fresh production
        # database could never be bootstrapped. Applying the policy here closes
        # that window, so this command leaves the database in the approved state
        # rather than one the next command refuses to load. `call_command`
        # defaults to skip_checks=True, which is what lets it run at all while
        # the placeholder rows still exist.
        if not dry_run:
            self.stdout.write("")
            call_command("apply_launch_policy", actor=options.get("actor", ""))

        self.stdout.write("")
        self.stdout.write("products seeded        : 0 (catalogue is filled in the admin)")
        self.stdout.write("reviews seeded         : 0")
        self.stdout.write("prototype notices      : none written")
        self.stdout.write(self.style.SUCCESS("launch baseline applied"))

    def _sanitise(self, data: dict) -> dict:
        """Strip every pre-launch claim from a copy of the fixture."""
        clean = copy.deepcopy(data)
        site = clean.setdefault("site", {})

        # 1. The storefront-wide "this is a preview; no real orders or payments"
        #    banner, rendered on cart and wishlist.
        site.pop("prototypeNotice", None)

        # 2. Copy that still calls the live free-shipping policy "planned".
        #    Applied to the whole tree, not just the announcement: the same
        #    claim also appears in the home hero metrics and the trust strip.
        self._replace_launch_text(clean)

        # 3. Placeholder contact details are worse than none: a customer who
        #    mails support@zakey.example or dials 0100 000 0000 gets silence and
        #    concludes the shop is abandoned. Blank fields let the template omit
        #    the row until the client enters the real ones in the admin.
        contact = site.get("contact")
        if isinstance(contact, dict):
            for field in ("email", "phoneDisplay", "hours"):
                if field in contact:
                    contact[field] = ""
            contact.pop("prototypeNotice", None)

        # 4. FAQ answers asserting that the shop cannot take an order.
        clean["faqs"] = [
            faq for faq in clean.get("faqs", []) if faq.get("id") not in LAUNCH_UNSAFE_FAQ_IDS
        ]

        # 5. Per-method payment notices; re-derived from the model in
        #    `_normalise_payment_notices` once the rows exist.
        for option in clean.get("paymentOptions", []):
            option.pop("prototypeNotice", None)

        # 6. Nothing below is read by the sections this command runs, but a
        #    fixture copy carrying prototype commerce state invites a later
        #    caller to reach for it.
        for key in ("products", "reviews", "prototypeAccounts", "prototypeCarts",
                    "prototypeWishlists", "couponPrototype"):
            clean.pop(key, None)
        clean["products"] = []
        clean["reviews"] = []

        return clean

    def _replace_launch_text(self, node):
        """Rewrite pre-launch phrasing in place, anywhere in the fixture tree.

        Returns the node so the caller can reassign list/scalar members; dicts
        and lists are edited in place.
        """
        if isinstance(node, dict):
            for key, value in node.items():
                node[key] = self._replace_launch_text(value)
        elif isinstance(node, list):
            for index, value in enumerate(node):
                node[index] = self._replace_launch_text(value)
        elif isinstance(node, str):
            return LAUNCH_TEXT_REPLACEMENTS.get(node, node)
        return node

    def _normalise_payment_notices(self) -> None:
        """Derive each notice from the model's own availability rule.

        `is_available_for_checkout` is the single source of truth for whether a
        method can be picked, so the customer-facing notice is computed from it
        rather than from a second hand-maintained list of codes.
        """
        from apps.payments.models import PaymentMethod

        for method in PaymentMethod.objects.all():
            notice = "" if method.is_available_for_checkout else UNAVAILABLE_PAYMENT_NOTICE
            if method.notice != notice:
                method.notice = notice
                method.save(update_fields=["notice", "updated_at"])


class _DryRun(Exception):
    """Rolls the transaction back once every section has reported."""
