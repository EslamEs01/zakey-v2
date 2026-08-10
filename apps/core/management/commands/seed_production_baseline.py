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

#: Site-wide banner while the demonstration catalogue is loaded. It names the
#: one thing a visitor could otherwise be misled by — the prices — rather than
#: claiming the shop does not work, which would be false: checkout is live.
DEMO_CATALOGUE_NOTICE = (
    "كتالوج عرض للمراجعة والتصميم. الأسعار والمواصفات المعروضة غير نهائية "
    "ولا تمثل عرضًا تجاريًا معتمدًا."
)


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
        parser.add_argument(
            "--with-demo-catalogue",
            action="store_true",
            help="Also import the fixture's products, collections, scenario cards and stock, "
            "plus a notice saying the prices are not approved. For design review only.",
        )
        parser.add_argument(
            "--without-demo-catalogue",
            action="store_true",
            help="Remove everything --with-demo-catalogue created and clear the notice.",
        )

    def handle(self, *args, **options):
        from apps.content.models import HomeSection

        from .seed_demo import FIXTURE, Command as SeedCommand, Report

        dry_run: bool = options["dry_run"]
        with_demo: bool = options["with_demo_catalogue"]
        without_demo: bool = options["without_demo_catalogue"]

        if with_demo and without_demo:
            raise CommandError("--with-demo-catalogue and --without-demo-catalogue are exclusive.")

        if without_demo:
            self._remove_demo_catalogue(dry_run)
            return

        if not FIXTURE.is_file():
            raise CommandError(f"Fixture not found: {FIXTURE}")

        seed_baseline = not HomeSection.objects.exists() or options["force"]
        if not seed_baseline and not with_demo:
            self.stdout.write(
                self.style.SUCCESS("baseline already applied; nothing to do (--force to reapply)")
            )
            return

        data = self._sanitise(
            json.loads(FIXTURE.read_text(encoding="utf-8")), keep_catalogue=with_demo
        )

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
                # Order follows seed_demo.handle: products must exist before
                # collections and cross-references can link to them, and the
                # FAQs that cross-references attach to come from _seed_content.
                if seed_baseline:
                    seeder._seed_settings(data)
                    seeder._seed_geography(data)
                    seeder._seed_shipping(data)
                    seeder._seed_payments(data)
                    seeder._seed_categories(data)
                if with_demo:
                    seeder._seed_products(data)
                # Without a demonstration catalogue these are empty containers:
                # `_seed_collections` skips product links whose product does not
                # exist, which is every one of them.
                if seed_baseline or with_demo:
                    seeder._seed_collections(data)
                if with_demo:
                    seeder._seed_reviews(data)
                if seed_baseline:
                    seeder._seed_content(data)
                if with_demo:
                    seeder._seed_cross_references(data)
                    seeder._seed_stock(data)
                self._normalise_payment_notices()
                self._set_catalogue_notice(DEMO_CATALOGUE_NOTICE if with_demo else "")
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

        self._report_state(with_demo)

    def _report_state(self, with_demo: bool) -> None:
        from apps.catalog.models import Product
        from apps.reviews.models import Review

        self.stdout.write("")
        if not with_demo:
            self.stdout.write("products seeded        : 0 (catalogue is filled in the admin)")
            self.stdout.write("reviews seeded         : 0")
            self.stdout.write("prototype notices      : none written")
            self.stdout.write(self.style.SUCCESS("launch baseline applied"))
            return

        self.stdout.write(f"products seeded        : {Product.objects.count()} (DEMONSTRATION)")
        self.stdout.write(f"scenario cards         : {Review.objects.count()}")
        self.stdout.write("catalogue notice       : shown site-wide")
        self.stdout.write(
            self.style.WARNING(
                "REVIEW STATE — these prices are not commercially approved. Keep the site "
                "excluded from search engines while this is in force, and run "
                "--without-demo-catalogue before the real catalogue goes in."
            )
        )

    def _set_catalogue_notice(self, notice: str) -> None:
        from apps.core.models import SiteSetting

        row = SiteSetting.objects.get_solo()
        if row.prototype_notice != notice:
            row.prototype_notice = notice
            row.save(update_fields=["prototype_notice", "updated_at"])

    def _remove_demo_catalogue(self, dry_run: bool) -> None:
        """Delete every row the demonstration catalogue created.

        Refuses once real orders exist: an order line references its product, so
        deleting the catalogue underneath it would either fail on the foreign key
        or destroy the record of what was sold.
        """
        from apps.catalog.models import Product
        from apps.orders.models import Order
        from apps.reviews.models import Review

        if Order.objects.exists():
            raise CommandError(
                f"Refusing to remove the catalogue: {Order.objects.count()} order(s) exist. "
                "Retire the individual products in the admin instead."
            )

        self.stdout.write(f"products to delete : {Product.objects.count()}")
        self.stdout.write(f"reviews to delete  : {Review.objects.count()}")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — nothing deleted."))
            return

        with transaction.atomic():
            Review.objects.all().delete()
            Product.objects.all().delete()
            self._set_catalogue_notice("")

        self.stdout.write("")
        self.stdout.write("catalogue notice   : cleared")
        self.stdout.write(self.style.SUCCESS("demonstration catalogue removed"))

    def _sanitise(self, data: dict, *, keep_catalogue: bool = False) -> dict:
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

        # 6. Prototype commerce state is never seeded, in either mode: those
        #    rows are fabricated identities, baskets and order history.
        for key in ("prototypeAccounts", "prototypeCarts", "prototypeWishlists",
                    "couponPrototype"):
            clean.pop(key, None)

        # 7. The catalogue itself. Kept only for a design review, where the
        #    products ARE the thing being reviewed and the notice set by
        #    `_set_catalogue_notice` tells visitors the prices are not final.
        if not keep_catalogue:
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
