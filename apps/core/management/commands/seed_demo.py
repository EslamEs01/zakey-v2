"""Idempotent development seed (FR-120 – FR-124).

Imports the approved storefront fixture into the database, preserving **every**
id, slug, Arabic string, image path and price so the storefront keeps rendering
identically and every existing URL keeps resolving (SC-011).

Two rules matter most:

* **Rerunning changes nothing.** Records are matched on their stable natural key
  (slug / key / code / legacy id) and updated in place. Never duplicated.
* **Prototype order history is NOT seeded as real orders** (ASM-007). Those
  fixture rows are inert display content with no lines, payment, address or
  status machine. Seeding them would fabricate revenue.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

#: Seed input only. This file is never read while serving a request (T-1608);
#: the storefront reads the database. `tests/fixtures/reference_catalogue.py`
#: reads the same file as the parity oracle so the two cannot drift.
FIXTURE = Path(settings.BASE_DIR) / "apps" / "core" / "seed_data" / "approved-catalogue.json"

#: Stock seeded per availability state so the catalogue filter behaves exactly
#: as `fixture_provider.py:183-190` does today.
STOCK_BY_AVAILABILITY = {"available": 25, "limited": 3, "unavailable": 0}


@dataclass
class Report:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    detail: dict[str, dict[str, int]] = field(default_factory=dict)

    def record(self, model: str, outcome: str) -> None:
        bucket = self.detail.setdefault(
            model, {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
        )
        bucket[outcome] += 1
        setattr(self, outcome, getattr(self, outcome) + 1)


class Command(BaseCommand):
    help = "Import the approved demonstration catalogue and content (development only)."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report without writing.")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Proceed even when real orders exist. Use with care.",
        )
        parser.add_argument(
            "--with-demo-customer",
            action="store_true",
            help="Also create the demonstration customer identity (never in production).",
        )

    def handle(self, *args, **options):
        self.dry_run: bool = options["dry_run"]
        self.verbosity: int = options.get("verbosity", 1)
        self.report = Report()

        if not FIXTURE.is_file():
            raise CommandError(f"Fixture not found: {FIXTURE}")

        from apps.orders.models import Order

        if Order.objects.exists() and not options["force"]:
            raise CommandError(
                f"Refusing to seed: {Order.objects.count()} real order(s) exist. "
                "Re-run with --force only if you are certain (FR-122)."
            )

        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        if data.get("meta", {}).get("fixtureStatus") != "demonstration":
            raise CommandError("Fixture is not marked as demonstration data.")

        try:
            with transaction.atomic():
                self._seed_settings(data)
                self._seed_geography(data)
                self._seed_shipping(data)
                self._seed_payments(data)
                self._seed_categories(data)
                self._seed_products(data)
                self._seed_collections(data)
                self._seed_reviews(data)
                self._seed_content(data)
                self._seed_cross_references(data)
                self._seed_stock(data)
                self._seed_demo_coupon(data)
                if self.dry_run:
                    raise _DryRun()
        except _DryRun:
            self.stdout.write(self.style.WARNING("DRY RUN — rolled back, nothing written."))

        self._print_report()

        if self.report.failed:
            raise CommandError(f"{self.report.failed} record(s) failed.")

    # -- sections ------------------------------------------------------------

    def _seed_settings(self, data):
        from apps.core.models import SiteSetting

        site = data["site"]
        obj = SiteSetting.objects.get_solo()
        obj.vat_rate = Decimal(str(site["vatRate"]))
        obj.free_shipping_threshold = Decimal(str(site["freeShippingThreshold"]))
        obj.currency_code = site["currency"]["code"]
        obj.currency_label = site["currency"]["label"]
        obj.currency_decimal_places = site["currency"]["decimalPlaces"]
        obj.prototype_notice = site.get("prototypeNotice", "")
        obj.save()
        self.report.record("SiteSetting", "updated")

    def _seed_geography(self, data):
        from apps.shipping.models import Governorate, ServiceArea

        for index, item in enumerate(data["governorates"]):
            _, created = Governorate.objects.update_or_create(
                key=item["key"],
                defaults={"name": item["label"], "position": index, "is_active": True},
            )
            self.report.record("Governorate", "created" if created else "updated")

        for item in data["serviceEligibility"]["areas"]:
            governorate = Governorate.objects.get(key=item["governorateKey"])
            _, created = ServiceArea.objects.update_or_create(
                key=item["key"],
                defaults={
                    "governorate": governorate,
                    "name": item["label"],
                    "same_day_eligible": item.get("sameDayEligible", False),
                    "installation_eligible": item.get("installationEligible", False),
                },
            )
            self.report.record("ServiceArea", "created" if created else "updated")

    def _seed_shipping(self, data):
        """Methods come from the fixture; PRICES do not exist there (ASM-004)."""
        from apps.shipping.models import (
            Governorate,
            InstallationService,
            ShippingMethod,
            ShippingRate,
            ShippingZone,
        )

        zone, created = ShippingZone.objects.get_or_create(
            name="كل المحافظات", defaults={"position": 0}
        )
        self.report.record("ShippingZone", "created" if created else "updated")
        zone.governorates.set(Governorate.objects.all())

        for index, option in enumerate(data["shippingOptions"]):
            eligibility = option.get("eligibility", {})
            method, created = ShippingMethod.objects.update_or_create(
                code=option["id"],
                defaults={
                    "label": option["label"],
                    "description": option.get("description", ""),
                    "icon_path": option.get("icon", {}).get("path", ""),
                    "requires_area_eligibility": eligibility.get("scope") == "configured-areas",
                    "free_over_threshold": "minimumSubtotal" in eligibility,
                    "position": index,
                },
            )
            self.report.record("ShippingMethod", "created" if created else "updated")

            # Development placeholders, explicitly flagged. Real commercial
            # rates are business input that does not exist yet (ASM-004).
            placeholder_price = Decimal("0.00") if method.free_over_threshold else Decimal("75.00")
            _, rate_created = ShippingRate.objects.update_or_create(
                method=method,
                zone=zone,
                defaults={
                    "price": placeholder_price,
                    "estimated_delivery_text": option.get("description", ""),
                    "is_placeholder": True,
                    "is_active": True,
                },
            )
            self.report.record("ShippingRate", "created" if rate_created else "updated")

        service, created = InstallationService.objects.update_or_create(
            name="خدمة التركيب",
            defaults={"fee": Decimal("250.00"), "is_placeholder": True, "is_active": True},
        )
        self.report.record("InstallationService", "created" if created else "updated")
        eligible_keys = data["serviceEligibility"]["installationGovernorateKeys"]
        service.governorates.set(Governorate.objects.filter(key__in=eligible_keys))

    def _seed_payments(self, data):
        """All six render; none is integrated (FR-071, FR-072)."""
        from apps.payments.models import PaymentMethod

        for index, option in enumerate(data["paymentOptions"]):
            code = option["id"]
            _, created = PaymentMethod.objects.update_or_create(
                code=code,
                defaults={
                    "label": option["label"],
                    "description": option.get("description", ""),
                    "icon_path": option.get("icon", {}).get("path", ""),
                    "notice": option.get("prototypeNotice", ""),
                    "is_active": True,
                    "is_integrated": False,
                    "collects_on_delivery": code == "payment-cod",
                    "is_manual": code
                    in {"payment-instapay", "payment-vodafone-cash", "payment-etisalat-cash"},
                    "position": index,
                },
            )
            self.report.record("PaymentMethod", "created" if created else "updated")

    def _seed_categories(self, data):
        from apps.catalog.models import Category
        from apps.core.models import PublicationStatus

        for index, item in enumerate(data["categories"]):
            _, created = Category.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "legacy_id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "kind": item.get("kind", ""),
                    "legacy_image_path": (item.get("image") or {}).get("path", ""),
                    "image_alt": (item.get("image") or {}).get("alt", ""),
                    "image_width": (item.get("image") or {}).get("width", 0),
                    "image_height": (item.get("image") or {}).get("height", 0),
                    "position": index,
                    "status": PublicationStatus.PUBLISHED,
                    "published_at": timezone.now(),
                },
            )
            self.report.record("Category", "created" if created else "updated")

    def _seed_products(self, data):
        from apps.catalog.models import (
            Category,
            Product,
            ProductDocument,
            ProductFeature,
            ProductImage,
            ProductVariant,
            SpecificationGroup,
            SpecificationItem,
        )
        from apps.core.models import PublicationStatus

        categories = {c.legacy_id: c for c in Category.objects.all()}

        for index, item in enumerate(data["products"]):
            category = categories[item["categoryId"]]
            product, created = Product.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "legacy_id": item["id"],
                    "name": item["name"],
                    "short_description": item.get("shortDescription", ""),
                    "category": category,
                    "badge": item.get("badge") or "",
                    "rating_average": Decimal(str(item.get("rating", 0))),
                    "review_count": item.get("reviewCount", 0),
                    "instalment_message": item.get("instalmentMessage", ""),
                    "same_day_supported": item.get("serviceFlags", {}).get(
                        "sameDaySupported", False
                    ),
                    "installation_supported": item.get("serviceFlags", {}).get(
                        "installationSupported", False
                    ),
                    "position": index,
                    "status": PublicationStatus.PUBLISHED,
                    "published_at": timezone.now(),
                },
            )
            self.report.record("Product", "created" if created else "updated")

            price = Decimal(str(item["price"]))
            compare_at = item.get("compareAtPrice")
            for v_index, finish in enumerate(item.get("finishes") or [{"id": "default", "label": ""}]):
                sku = self._sku(item["slug"], finish["id"])
                _, v_created = ProductVariant.objects.update_or_create(
                    sku=sku,
                    defaults={
                        "product": product,
                        "finish_id": finish["id"],
                        "finish_label": finish.get("label", ""),
                        "swatch_hex": finish.get("swatch", ""),
                        "price": price,
                        "compare_at_price": Decimal(str(compare_at)) if compare_at else None,
                        "position": v_index,
                        "is_default": v_index == 0,
                        "is_active": True,
                    },
                )
                self.report.record("ProductVariant", "created" if v_created else "updated")

            for i_index, image in enumerate(item.get("images", [])):
                _, i_created = ProductImage.objects.update_or_create(
                    product=product,
                    legacy_id=image["id"],
                    defaults={
                        "legacy_path": image["path"],
                        "alt": image.get("alt", product.name),
                        "width": image.get("width", 0),
                        "height": image.get("height", 0),
                        "position": i_index,
                    },
                )
                self.report.record("ProductImage", "created" if i_created else "updated")

            for f_index, feature in enumerate(item.get("features", [])):
                _, f_created = ProductFeature.objects.update_or_create(
                    product=product,
                    key=feature["key"],
                    defaults={
                        "label": feature["label"],
                        "description": feature.get("description", ""),
                        "position": f_index,
                    },
                )
                self.report.record("ProductFeature", "created" if f_created else "updated")

            for g_index, group in enumerate(item.get("specificationGroups", [])):
                spec_group, g_created = SpecificationGroup.objects.update_or_create(
                    product=product,
                    legacy_id=group["id"],
                    defaults={"label": group["label"], "position": g_index},
                )
                self.report.record("SpecificationGroup", "created" if g_created else "updated")
                spec_group.items.all().delete()
                for s_index, spec in enumerate(group.get("items", [])):
                    SpecificationItem.objects.create(
                        group=spec_group,
                        label=spec["label"],
                        value=spec["value"],
                        position=s_index,
                    )

            for d_index, doc in enumerate(item.get("downloads", [])):
                _, d_created = ProductDocument.objects.update_or_create(
                    product=product,
                    legacy_id=doc["id"],
                    defaults={
                        "label": doc["label"],
                        "legacy_path": doc["path"],
                        "file_format": doc.get("format", "PDF"),
                        "notice": doc.get("prototypeNotice", "")[:255],
                        "position": d_index,
                    },
                )
                self.report.record("ProductDocument", "created" if d_created else "updated")

    @staticmethod
    def _sku(product_slug: str, finish_id: str) -> str:
        """Deterministic, so re-running produces the same SKU (INV-008)."""
        tail = finish_id.split("-")[-1].upper() if finish_id else "STD"
        return f"ZK-{product_slug.upper()}-{tail}"

    def _seed_collections(self, data):
        from apps.catalog.models import Collection, CollectionProduct, Product
        from apps.core.models import PublicationStatus

        products = {p.legacy_id: p for p in Product.objects.all()}
        for index, item in enumerate(data["collections"]):
            collection, created = Collection.objects.update_or_create(
                slug=item["slug"],
                defaults={
                    "legacy_id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "promotion_eyebrow": (item.get("promotion") or {}).get("eyebrow", ""),
                    "promotion_tone": (item.get("promotion") or {}).get("tone", ""),
                    "position": index,
                    "status": PublicationStatus.PUBLISHED,
                    "published_at": timezone.now(),
                },
            )
            self.report.record("Collection", "created" if created else "updated")

            CollectionProduct.objects.filter(collection=collection).delete()
            for p_index, product_legacy_id in enumerate(item.get("productIds", [])):
                product = products.get(product_legacy_id)
                if product is None:
                    self.report.record("CollectionProduct", "skipped")
                    continue
                CollectionProduct.objects.create(
                    collection=collection, product=product, position=p_index
                )

    def _seed_reviews(self, data):
        from apps.catalog.models import Product
        from apps.reviews.models import Review, ReviewStatus

        products = {p.legacy_id: p for p in Product.objects.all()}
        for item in data["reviews"]:
            product = products.get(item["productId"])
            if product is None:
                self.report.record("Review", "skipped")
                continue
            _, created = Review.objects.update_or_create(
                legacy_id=item["id"],
                defaults={
                    "product": product,
                    "author_name": item["customerName"],
                    "rating": item["rating"],
                    "body": item["quote"],
                    # The storefront renders a short attribution line under the
                    # quote. Demo rows carry the prototype disclaimer; real
                    # customer reviews will carry their own title here.
                    "title": item.get("prototypeAttribution", "")[:160],
                    "placement": item.get("placement", []),
                    "status": ReviewStatus.APPROVED,
                    "is_verified_purchase": False,
                },
            )
            self.report.record("Review", "created" if created else "updated")

    def _seed_content(self, data):
        from apps.content.models import FAQ, NavigationItem, NavigationGroup, Partner

        for index, item in enumerate(data["faqs"]):
            _, created = FAQ.objects.update_or_create(
                legacy_id=item["id"],
                defaults={
                    "question": item["question"],
                    "answer": item["answer"],
                    "page": item.get("page", ""),
                    "position": index,
                    "is_active": True,
                },
            )
            self.report.record("FAQ", "created" if created else "updated")

        for index, item in enumerate(data["partners"]):
            asset = item.get("mark") or item.get("image") or {}
            _, created = Partner.objects.update_or_create(
                name=item["name"],
                defaults={
                    "legacy_image_path": asset.get("path", "") if isinstance(asset, dict) else "",
                    "position": index,
                    "is_active": True,
                },
            )
            self.report.record("Partner", "created" if created else "updated")

        navigation = data.get("navigation", {})
        for group_name, group_enum in (
            ("primary", NavigationGroup.PRIMARY),
            ("utility", NavigationGroup.UTILITY),
        ):
            for index, item in enumerate(navigation.get(group_name, [])):
                _, created = NavigationItem.objects.update_or_create(
                    label=item["label"],
                    group=group_enum,
                    defaults={
                        "href": item.get("href", ""),
                        "icon": item.get("icon", ""),
                        "position": index,
                        "is_active": True,
                    },
                )
                self.report.record("NavigationItem", "created" if created else "updated")

        self._seed_page_copy(data)

    #: Authored page copy that the storefront used to read straight out of the
    #: JSON fixture at request time. Each key becomes one staff-editable
    #: ``HomeSection`` row carrying its structured payload (T-1205, T-1608).
    #: ``prototypeAccounts`` / ``prototypeCarts`` / ``prototypeWishlists`` /
    #: ``couponPrototype`` are deliberately NOT among them: those are prototype
    #: commerce state, now owned by accounts, cart and promotions respectively.
    PAGE_COPY_SECTIONS = ("brand", "announcement", "home", "about", "contact", "footer")

    def _seed_page_copy(self, data):
        from apps.content.models import HomeSection, StaticPage

        site = data.get("site", {})
        for index, key in enumerate(self.PAGE_COPY_SECTIONS):
            payload = site.get(key)
            if payload is None:
                continue
            if not isinstance(payload, dict):
                payload = {"value": payload}
            _, created = HomeSection.objects.update_or_create(
                key=key,
                defaults={
                    "heading": (payload.get("heading") or "")[:160],
                    "eyebrow": (payload.get("eyebrow") or "")[:120],
                    "data": payload,
                    "position": index,
                    "is_active": True,
                },
            )
            self.report.record("HomeSection", "created" if created else "updated")

        # The about page renders a team roster; it is presentation copy, so it
        # travels with the about section rather than earning its own model.
        if data.get("team"):
            _, created = HomeSection.objects.update_or_create(
                key="team",
                defaults={
                    "heading": site.get("about", {}).get("teamHeading", "")[:160],
                    "data": {"members": data["team"]},
                    "position": len(self.PAGE_COPY_SECTIONS),
                    "is_active": True,
                },
            )
            self.report.record("HomeSection", "created" if created else "updated")

        for slug, title in (("about", "عن ZAKEY"), ("contact", "تواصل معنا")):
            _, created = StaticPage.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": site.get(slug, {}).get("heading") or title,
                    "seo_description": site.get(slug, {}).get("description", "")[:255],
                    "is_published": True,
                },
            )
            self.report.record("StaticPage", "created" if created else "updated")

    def _seed_cross_references(self, data):
        from apps.catalog.models import Product, ProductRelation
        from apps.content.models import FAQ

        products = {p.legacy_id: p for p in Product.objects.all()}
        faqs = {f.legacy_id: f for f in FAQ.objects.all()}

        for item in data["products"]:
            product = products.get(item["id"])
            if product is None:
                continue
            ProductRelation.objects.filter(from_product=product).delete()
            for index, related_id in enumerate(item.get("relatedProductIds", [])):
                related = products.get(related_id)
                if related is None or related.pk == product.pk:
                    self.report.record("ProductRelation", "skipped")
                    continue
                ProductRelation.objects.create(
                    from_product=product, to_product=related, position=index
                )
            for faq_id in item.get("faqIds", []):
                faq = faqs.get(faq_id)
                if faq is not None:
                    faq.products.add(product)

    def _seed_stock(self, data):
        """Derived from fixture availability so catalogue filters match."""
        from apps.catalog.models import Product
        from apps.inventory.models import StockItem

        products = {p.legacy_id: p for p in Product.objects.prefetch_related("variants")}
        for item in data["products"]:
            product = products.get(item["id"])
            if product is None:
                continue
            on_hand = STOCK_BY_AVAILABILITY.get(item.get("availability", "available"), 25)
            for variant in product.variants.all():
                stock, created = StockItem.objects.get_or_create(
                    variant=variant, defaults={"on_hand": on_hand, "reserved": 0}
                )
                if not created and stock.reserved == 0 and stock.on_hand != on_hand:
                    stock.on_hand = on_hand
                    stock.save(update_fields=["on_hand", "updated_at"])
                self.report.record("StockItem", "created" if created else "updated")

    def _seed_demo_coupon(self, data):
        """ZAKEYDEMO is demonstration data, never a real commercial offer."""
        from apps.promotions.models import Coupon, DiscountType

        if not settings.DEBUG and not getattr(settings, "ZAKEY_ALLOW_PLACEHOLDER_RATES", False):
            self.report.record("Coupon", "skipped")
            return

        prototype = data["site"].get("couponPrototype")
        if not prototype:
            return
        _, created = Coupon.objects.update_or_create(
            code=prototype["acceptedCode"].upper(),
            defaults={
                "discount_type": DiscountType.PERCENTAGE,
                "value": Decimal(str(prototype["discountRate"])) * Decimal("100"),
                "description": prototype.get("prototypeNotice", ""),
                "is_active": True,
                "is_demo": True,
            },
        )
        self.report.record("Coupon", "created" if created else "updated")

    # -- reporting -----------------------------------------------------------

    def _print_report(self):
        # Honour --verbosity 0. Tests call this command as a fixture; a report
        # per test drowns the actual test output.
        if getattr(self, "verbosity", 1) < 1:
            return
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("seed_demo report"))
        for model in sorted(self.report.detail):
            counts = self.report.detail[model]
            self.stdout.write(
                f"  {model:<22} created={counts['created']:<4} updated={counts['updated']:<4} "
                f"skipped={counts['skipped']:<4} failed={counts['failed']}"
            )
        self.stdout.write("")
        self.stdout.write(
            f"TOTAL created={self.report.created} updated={self.report.updated} "
            f"skipped={self.report.skipped} failed={self.report.failed}"
        )
        self.stdout.write(
            self.style.WARNING(
                "Shipping and installation prices are DEVELOPMENT PLACEHOLDERS "
                "(ASM-004/ASM-005) and are not commercially approved."
            )
        )
        self.stdout.write(
            self.style.WARNING(
                "Prototype order history was NOT seeded as real orders (ASM-007)."
            )
        )


class _DryRun(Exception):
    """Internal signal used to roll back a dry run."""
