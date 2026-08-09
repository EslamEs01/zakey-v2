"""The demonstration seed, measured against the fixture it imports (T-1501 – T-1506).

``seed_demo`` is the only path by which the approved prototype's content becomes
database rows. Everything downstream — the storefront parity suite, the route
contract, the browser gate — is measured against a database this command wrote,
so an unfaithful or non-idempotent import would silently move the baseline every
other suite trusts.

The assertions here are therefore about *fidelity and restraint*: every value
survives unchanged, a second run changes nothing, the demonstration rows stay
labelled as demonstration rows, and the sections the migration map excludes stay
excluded. The slug lists are frozen literals rather than values read back out of
the fixture, because an expectation derived from the same file the importer
reads would pass even if both changed together — which is precisely the failure
it exists to catch.
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.cart.models import Cart, Wishlist
from apps.catalog.models import (
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductVariant,
)
from apps.content.models import FAQ, Partner
from apps.core.management.commands import seed_demo
from apps.orders.models import Order
from apps.payments.models import PaymentMethod
from apps.promotions.models import Coupon
from apps.reviews.models import Review
from apps.shipping.models import (
    Governorate,
    InstallationService,
    ServiceArea,
    ShippingMethod,
    ShippingRate,
)

pytestmark = pytest.mark.django_db

FIXTURE_PATH = (
    Path(settings.BASE_DIR) / "apps" / "core" / "seed_data" / "approved-catalogue.json"
)
FIXTURE = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

#: The URL contract, frozen (`frontend-contract.md` §2). Changing any of these
#: strings breaks a live address, so the list is written out by hand.
PRODUCT_SLUGS = [
    "zakey-apex-pro",
    "zakey-nexus-elite",
    "zakey-vision-x",
    "zakey-pulse-f5",
    "zakey-orbit-k3",
    "zakey-nova-s2",
    "zakey-core-c1",
    "zakey-guard-view",
    "zakey-bridge-mini",
]
COLLECTION_SLUGS = [
    "best-sellers",
    "featured",
    "fingerprint-locks",
    "security-accessories",
    "smart-door-locks",
    "smart-home-solutions",
]
CATEGORY_SLUGS = ["accessories", "fingerprint", "keypad", "smart-handle"]


def run(*args) -> str:
    """Run the command at default verbosity and return its report."""
    out = StringIO()
    call_command("seed_demo", *args, stdout=out, stderr=StringIO())
    return out.getvalue()


def counts_for(model: str, report: str) -> tuple[int, int]:
    """``(created, updated)`` for one model, read off the printed report."""
    match = re.search(
        rf"^\s*{model}\s+created=(\d+)\s+updated=(\d+)", report, re.MULTILINE
    )
    assert match, f"the report has no line for {model}:\n{report}"
    return int(match.group(1)), int(match.group(2))


def row_counts() -> dict[str, int]:
    return {
        model.__name__: model.objects.count()
        for model in (
            Category,
            Collection,
            CollectionProduct,
            Product,
            ProductVariant,
            Review,
            FAQ,
            Partner,
            Governorate,
            ServiceArea,
            ShippingMethod,
            ShippingRate,
            PaymentMethod,
        )
    }


def catalogue_snapshot() -> list[tuple]:
    """Every value the fixture owns, in a form two runs can be compared on."""
    return [
        (
            product.slug,
            product.legacy_id,
            product.name,
            product.short_description,
            product.instalment_message,
            tuple(sorted((v.sku, str(v.price)) for v in product.variants.all())),
            tuple((image.legacy_path, image.alt) for image in product.images.all()),
        )
        for product in Product.objects.order_by("slug").prefetch_related(
            "variants", "images"
        )
    ]


def make_real_order() -> Order:
    return Order.objects.create(
        number="ZK-REAL-1",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="key-ZK-REAL-1",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


# ---------------------------------------------------------------------------
# Slugs
# ---------------------------------------------------------------------------


class TestSlugContract:
    """Product slugs are unique and stable, and all nine product, six
    collection and four category slugs survive the import exactly (FR-011).

    Stability is not the same as presence: a re-import that dropped and
    recreated a row would keep the slug and still break every foreign key and
    bookmark pointing at it, so identity is checked as well.
    """

    def test_the_nine_product_slugs_are_preserved_exactly(self, seeded_catalogue):
        assert sorted(Product.objects.values_list("slug", flat=True)) == sorted(
            PRODUCT_SLUGS
        )

    def test_the_six_collection_slugs_are_preserved_exactly(self, seeded_catalogue):
        assert sorted(Collection.objects.values_list("slug", flat=True)) == COLLECTION_SLUGS

    def test_the_four_category_slugs_are_preserved_exactly(self, seeded_catalogue):
        assert sorted(Category.objects.values_list("slug", flat=True)) == CATEGORY_SLUGS

    def test_a_second_import_keeps_every_slug_on_its_original_row(self, seeded_catalogue):
        before = dict(Product.objects.values_list("slug", "id"))

        run()

        assert dict(Product.objects.values_list("slug", "id")) == before

    def test_the_database_refuses_a_duplicate_product_slug(self, seeded_catalogue):
        existing = Product.objects.get(slug="zakey-apex-pro")

        with pytest.raises(IntegrityError), transaction.atomic():
            Product.objects.create(
                slug="zakey-apex-pro", name="نسخة مكررة", category=existing.category
            )

        assert Product.objects.filter(slug="zakey-apex-pro").count() == 1


# ---------------------------------------------------------------------------
# Fidelity
# ---------------------------------------------------------------------------


class TestFixtureValuesSurviveTheImport:
    """The import preserves every id, slug, image path, Arabic string and price
    the approved fixture holds (FR-120).

    Arabic strings are asserted verbatim rather than by length or truthiness: a
    mangled encoding, a truncated field or an accidental ``strip()`` would all
    pass a weaker check and be visible to a customer on the first page load.
    """

    def test_every_product_keeps_its_id_slug_and_arabic_copy(self, seeded_catalogue):
        for item in FIXTURE["products"]:
            product = Product.objects.get(slug=item["slug"])

            assert product.legacy_id == item["id"]
            assert product.name == item["name"]
            assert product.short_description == item["shortDescription"]
            assert product.instalment_message == item["instalmentMessage"]

    def test_every_price_is_preserved_exactly(self, seeded_catalogue):
        for item in FIXTURE["products"]:
            product = Product.objects.get(slug=item["slug"])
            expected = Decimal(str(item["price"]))

            for variant in product.variants.all():
                assert variant.price == expected, f"{variant.sku} was re-priced"

            expected_compare = (
                Decimal(str(item["compareAtPrice"]))
                if item["compareAtPrice"] is not None
                else None
            )
            assert product.compare_at_price == expected_compare

    def test_every_image_path_and_arabic_alt_survives_in_order(self, seeded_catalogue):
        for item in FIXTURE["products"]:
            images = list(Product.objects.get(slug=item["slug"]).images.all())

            assert [image.legacy_path for image in images] == [
                source["path"] for source in item["images"]
            ]
            assert [image.alt for image in images] == [
                source["alt"] for source in item["images"]
            ]

    def test_categories_and_collections_keep_their_arabic_names(self, seeded_catalogue):
        for item in FIXTURE["categories"]:
            assert Category.objects.get(slug=item["slug"]).name == item["name"]
        for item in FIXTURE["collections"]:
            assert Collection.objects.get(slug=item["slug"]).name == item["name"]

    def test_a_second_import_leaves_every_value_identical(self, seeded_catalogue):
        before = catalogue_snapshot()

        run()

        assert catalogue_snapshot() == before


# ---------------------------------------------------------------------------
# Idempotence and reporting
# ---------------------------------------------------------------------------


class TestRerunningIsSafeAndReported:
    """Rerunning duplicates nothing, and the command reports created, updated,
    skipped and failed counts (FR-121).

    The counts are checked against a first and a second run rather than merely
    checked for presence, because a report that always prints the same numbers
    is worse than no report — it looks like evidence.
    """

    def test_a_second_run_creates_no_new_rows(self, seeded_catalogue):
        before = row_counts()

        run()

        assert row_counts() == before

    def test_the_report_names_created_updated_skipped_and_failed(self, seeded_catalogue):
        report = run()

        assert re.search(
            r"TOTAL created=\d+ updated=\d+ skipped=\d+ failed=\d+", report
        ), report
        for outcome in ("created=", "updated=", "skipped=", "failed="):
            assert outcome in report

    def test_a_first_run_reports_the_records_it_created(self, db):
        report = run()

        assert counts_for("Product", report) == (9, 0)
        assert counts_for("Category", report) == (4, 0)

    def test_a_second_run_reports_updates_rather_than_creations(self, seeded_catalogue):
        report = run()

        assert counts_for("Product", report) == (0, 9)
        assert counts_for("Category", report) == (0, 4)


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


class TestSeedingRefusesToTouchRealCommerce:
    """The command refuses to run once real orders exist unless it is explicitly
    forced, and nothing runs it automatically (FR-122).

    An automatic invocation is the dangerous case: a seed wired into a migration
    or an ``AppConfig.ready`` would run on the next production deploy with
    nobody's hand on it, which is why that is asserted structurally rather than
    left to convention.
    """

    def test_seeding_is_refused_when_an_order_exists(self, db):
        make_real_order()

        with pytest.raises(CommandError) as caught:
            run()

        assert "Refusing to seed" in str(caught.value)
        assert not Product.objects.exists(), "the refusal still wrote catalogue rows"

    def test_a_refused_run_leaves_the_order_untouched(self, db):
        order = make_real_order()

        with pytest.raises(CommandError):
            run()

        order.refresh_from_db()
        assert order.grand_total == Decimal("7490.00")
        assert Order.objects.count() == 1

    def test_force_overrides_the_refusal(self, db):
        make_real_order()

        run("--force")

        assert Product.objects.count() == 9

    def test_nothing_runs_the_seed_automatically(self):
        root = Path(settings.BASE_DIR)
        automatic = [
            *root.glob("apps/*/migrations/*.py"),
            *root.glob("apps/*/apps.py"),
            *root.glob("config/settings/*.py"),
            root / "manage.py",
            root / "config" / "wsgi.py",
            root / "config" / "asgi.py",
        ]

        offenders = [
            str(path.relative_to(root))
            for path in automatic
            if path.is_file() and "seed_demo" in path.read_text(encoding="utf-8")
        ]

        assert offenders == [], (
            f"these run on migrate or on startup and reference the seed: {offenders}"
        )


# ---------------------------------------------------------------------------
# Demonstration content is labelled
# ---------------------------------------------------------------------------


class TestDemoContentIsDistinguishable:
    """Seeded demonstration content is distinguishable from production content
    (FR-123).

    A label nobody reads is decoration, so the enforcement is asserted too: the
    system must refuse to quote a placeholder price as though it were a real
    one.
    """

    def test_every_seeded_commercial_price_is_flagged_as_a_placeholder(
        self, seeded_catalogue
    ):
        assert ShippingRate.objects.exists()
        assert not ShippingRate.objects.filter(is_placeholder=False).exists()
        assert InstallationService.objects.exists()
        assert not InstallationService.objects.filter(is_placeholder=False).exists()

    def test_the_seeded_coupon_is_flagged_as_a_demonstration_offer(self, seeded_catalogue):
        coupon = Coupon.objects.get(code="ZAKEYDEMO")

        assert coupon.is_demo is True
        assert not Coupon.objects.filter(is_demo=False).exists()

    def test_a_placeholder_price_cannot_be_quoted_as_a_real_one(
        self, seeded_catalogue, settings
    ):
        from apps.shipping import services as shipping_services

        settings.ZAKEY_ALLOW_PLACEHOLDER_RATES = False

        with pytest.raises(shipping_services.PlaceholderRateError):
            shipping_services.quote_shipping(
                ShippingMethod.objects.get(code="shipping-standard"),
                Governorate.objects.get(key="cairo"),
                None,
                Decimal("100.00"),
            )

    def test_a_fixture_not_marked_as_demonstration_is_refused(
        self, db, tmp_path, monkeypatch
    ):
        payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        payload["meta"]["fixtureStatus"] = "production"
        impostor = tmp_path / "not-demonstration.json"
        impostor.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        monkeypatch.setattr(seed_demo, "FIXTURE", impostor)

        with pytest.raises(CommandError) as caught:
            run()

        assert "demonstration" in str(caught.value)
        assert not Product.objects.exists()


# ---------------------------------------------------------------------------
# The documented mapping
# ---------------------------------------------------------------------------


class TestMappingFollowsTheDocumentedMap:
    """Every fixture section lands where `fixture-migration-map.md` says it
    lands, field for field (FR-124).

    The map is not decorative: it is what the parity suite, the SKU scheme and
    the availability filter were all derived from, so a drift between the map
    and the importer invalidates them together.
    """

    def test_each_section_lands_in_the_model_the_map_names(self, seeded_catalogue):
        assert Category.objects.count() == len(FIXTURE["categories"]) == 4
        assert Collection.objects.count() == len(FIXTURE["collections"]) == 6
        assert Product.objects.count() == len(FIXTURE["products"]) == 9
        assert Review.objects.count() == len(FIXTURE["reviews"]) == 9
        assert FAQ.objects.count() == len(FIXTURE["faqs"]) == 8
        assert Partner.objects.count() == len(FIXTURE["partners"]) == 4
        assert Governorate.objects.count() == len(FIXTURE["governorates"]) == 27
        assert ServiceArea.objects.count() == len(FIXTURE["serviceEligibility"]["areas"]) == 14
        assert ShippingMethod.objects.count() == len(FIXTURE["shippingOptions"]) == 3
        assert PaymentMethod.objects.count() == len(FIXTURE["paymentOptions"]) == 6

    def test_a_product_maps_field_by_field(self, seeded_catalogue):
        for item in FIXTURE["products"]:
            product = Product.objects.get(slug=item["slug"])

            assert product.category.legacy_id == item["categoryId"]
            assert product.badge == (item["badge"] or "")
            assert product.review_count == item["reviewCount"]
            assert product.same_day_supported == item["serviceFlags"]["sameDaySupported"]
            assert (
                product.installation_supported
                == item["serviceFlags"]["installationSupported"]
            )
            assert {
                membership.collection.legacy_id
                for membership in product.collectionproduct_set.all()
            } == set(item["collectionIds"])

            variants = list(product.variants.all())
            assert [v.finish_id for v in variants] == [f["id"] for f in item["finishes"]]
            assert [v.finish_label for v in variants] == [
                f["label"] for f in item["finishes"]
            ]
            assert [v.swatch_hex for v in variants] == [
                f["swatch"] for f in item["finishes"]
            ]
            assert [v.position for v in variants] == list(range(len(variants)))
            assert [v.is_default for v in variants] == [True] + [False] * (
                len(variants) - 1
            )

            images = list(product.images.all())
            assert [i.legacy_id for i in images] == [x["id"] for x in item["images"]]
            assert [i.position for i in images] == list(range(len(images)))

            features = list(product.features.all())
            assert [f.key for f in features] == [x["key"] for x in item["features"]]
            assert [f.label for f in features] == [x["label"] for x in item["features"]]
            assert [f.description for f in features] == [
                x["description"] for x in item["features"]
            ]

    def test_collection_membership_keeps_the_fixture_order(self, seeded_catalogue):
        for item in FIXTURE["collections"]:
            collection = Collection.objects.get(slug=item["slug"])
            members = CollectionProduct.objects.filter(collection=collection).order_by(
                "position"
            )

            assert [member.product.legacy_id for member in members] == item["productIds"]
            assert [member.position for member in members] == list(
                range(len(item["productIds"]))
            )

    def test_the_sku_follows_the_documented_formula(self, seeded_catalogue):
        for item in FIXTURE["products"]:
            for finish in item["finishes"]:
                expected = (
                    f"ZK-{item['slug'].upper()}-{finish['id'].split('-')[-1].upper()}"
                )
                assert ProductVariant.objects.filter(
                    sku=expected, product__slug=item["slug"]
                ).exists(), f"{item['slug']} / {finish['id']} did not produce {expected}"

    @pytest.mark.parametrize(
        "availability, on_hand", [("available", 25), ("limited", 3), ("unavailable", 0)]
    )
    def test_stock_is_derived_from_availability_as_the_map_says(
        self, seeded_catalogue, availability, on_hand
    ):
        slugs = [p["slug"] for p in FIXTURE["products"] if p["availability"] == availability]
        assert slugs, f"the fixture no longer exercises {availability}"

        for slug in slugs:
            for variant in Product.objects.get(slug=slug).variants.all():
                assert variant.stock_item.on_hand == on_hand

    def test_the_sections_the_map_excludes_are_not_seeded(self, seeded_catalogue):
        """Seeding these would fabricate customers, baskets and revenue."""
        demo_identity = next(
            account["identity"]
            for account in FIXTURE["prototypeAccounts"]
            if account.get("identity")
        )

        assert Order.objects.count() == 0
        assert Cart.objects.count() == 0
        assert Wishlist.objects.count() == 0
        assert not User.objects.filter(email=demo_identity["email"]).exists()
