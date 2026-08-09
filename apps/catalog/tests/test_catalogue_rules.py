"""Catalogue rules the approved storefront depends on (T-0503 – T-0505).

``test_archive_policy`` covers the archive-not-delete half of the catalogue
lifecycle. This file covers the other rules the storefront contract assumes and
that nothing else asserts: SKU identity, publication visibility, product
completeness, explicit ordering, price ownership, and the merchandising fields
the product page renders.

Several of these are database guarantees rather than form validation, and the
distinction is load-bearing: the importer, the shell and ``bulk_create`` all
write rows without ever calling ``Model.full_clean``. Those tests therefore go
through ``objects.create`` deliberately, so a passing assertion means the
*table* refused the row.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib import admin as django_admin
from django.db import IntegrityError, connection, transaction
from django.test import RequestFactory

from apps.catalog import selectors
from apps.catalog.admin import ProductImageInline, ProductVariantInline
from apps.catalog.models import Product, ProductFeature, ProductImage, ProductVariant
from apps.core.models import PublicationStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def staff_request(db):
    """A request from a superuser, for asking the admin what staff may edit."""
    from apps.accounts.models import User

    request = RequestFactory().get("/admin/catalog/product/")
    request.user = User.objects.create_superuser(
        email="admin@zakey.invalid", password="StrongPass!234"
    )
    return request


# ---------------------------------------------------------------------------
# SKU identity
# ---------------------------------------------------------------------------


class TestVariantSkuIdentity:
    """SKU identifies the thing that is actually picked, packed and sold, so it
    must be unique across the whole catalogue and not merely within a product
    (FR-012). Uniqueness is asserted at the database because that is the only
    layer every writer passes through.
    """

    def test_a_duplicate_sku_under_another_product_is_rejected(self, product, variant, category):
        other = Product.objects.create(
            slug="zakey-lite", name="قفل زاكي لايت", category=category
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            ProductVariant.objects.create(
                product=other,
                sku=variant.sku,
                finish_id="finish-obsidian",
                price=Decimal("1000.00"),
            )

        assert ProductVariant.objects.filter(sku=variant.sku).count() == 1

    def test_a_duplicate_sku_under_the_same_product_is_rejected(self, product, variant):
        with pytest.raises(IntegrityError), transaction.atomic():
            ProductVariant.objects.create(
                product=product, sku=variant.sku, price=Decimal("1000.00")
            )

        assert ProductVariant.objects.filter(sku=variant.sku).count() == 1

    def test_the_uniqueness_is_declared_on_the_table(self):
        """Names the constraint that produced the refusals above.

        ``objects.create`` never validates, so those errors can only have come
        from PostgreSQL — this asserts the index is really there rather than
        inferring it from an exception type.
        """
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor, ProductVariant._meta.db_table
            )

        unique_on_sku = [
            name
            for name, spec in constraints.items()
            if spec["unique"] and spec["columns"] == ["sku"]
        ]
        assert unique_on_sku, f"no unique database constraint on sku: {sorted(constraints)}"


# ---------------------------------------------------------------------------
# Publication lifecycle
# ---------------------------------------------------------------------------


class TestPublicationVisibility:
    """Products carry a draft / published / archived lifecycle and only the
    published ones are visible on the storefront (FR-013).

    Visibility is checked through the selectors rather than a template, because
    the selectors are what every storefront view reads: a direct URL must not
    reveal what the list hides.
    """

    def test_the_lifecycle_has_exactly_the_three_documented_states(self):
        assert [state.value for state in PublicationStatus] == [
            "draft",
            "published",
            "archived",
        ]

    @pytest.mark.parametrize(
        "status, visible",
        [
            (PublicationStatus.DRAFT, False),
            (PublicationStatus.PUBLISHED, True),
            (PublicationStatus.ARCHIVED, False),
        ],
    )
    def test_only_published_products_reach_the_storefront(
        self, product, variant, stock, status, visible
    ):
        product.status = status
        product.save(update_fields=["status"])

        listed = [item["slug"] for item in selectors.get_catalogue({})["products"]]
        detail = selectors.get_product_detail(product.slug)

        assert (product.slug in listed) is visible
        assert (detail is not None) is visible


# ---------------------------------------------------------------------------
# Product completeness
# ---------------------------------------------------------------------------


class TestProductCompleteness:
    """Every product has at least one image and at least one variant, and the
    first of each is the one the storefront picks (FR-015).

    The approved product page indexes ``images[0]`` and ``finishes[0]`` with no
    guard, so "at least one" is a hard invariant rather than a nicety, and
    "first" means first by explicit position, not by insertion order.
    """

    def test_every_catalogue_product_has_an_image_and_a_variant(self, seeded_catalogue):
        for product in Product.objects.published().prefetch_related("images", "variants"):
            assert product.images.exists(), f"{product.slug} has no image"
            assert product.variants.exists(), f"{product.slug} has no variant"

    def test_the_primary_image_is_the_first_by_position_not_by_insertion(self, product):
        ProductImage.objects.create(
            product=product, legacy_path="/static/c.webp", alt="ج", position=2
        )
        first = ProductImage.objects.create(
            product=product, legacy_path="/static/a.webp", alt="أ", position=0
        )
        ProductImage.objects.create(
            product=product, legacy_path="/static/b.webp", alt="ب", position=1
        )

        assert Product.objects.get(pk=product.pk).primary_image.pk == first.pk

    def test_the_default_variant_is_the_first_by_position(
        self, product, variant, second_variant
    ):
        # Clear the explicit flag: the first ordered finish must still be the
        # one a customer lands on, or an unflagged import would sell the wrong
        # variant by default.
        variant.is_default = False
        variant.save(update_fields=["is_default"])

        assert Product.objects.get(pk=product.pk).default_variant.pk == variant.pk

    def test_the_seeded_catalogue_flags_its_first_finish_as_default(self, seeded_catalogue):
        for product in Product.objects.published().prefetch_related("variants"):
            ordered = list(product.variants.all())
            assert ordered[0].is_default, f"{product.slug} does not default to its first finish"
            assert product.default_variant.pk == ordered[0].pk


# ---------------------------------------------------------------------------
# Ordering
# ---------------------------------------------------------------------------


class TestOrderingIsExplicitAndStaffControllable:
    """Image and variant order is a stored number a member of staff can change,
    not an accident of insertion order (FR-016).

    Both halves matter: "explicit" means editing ``position`` changes what the
    storefront renders, and "staff-controllable" means the admin form actually
    offers that field for editing.
    """

    def test_reordering_images_changes_what_the_storefront_renders_first(
        self, product, variant
    ):
        first = ProductImage.objects.create(
            product=product, legacy_path="/static/a.webp", alt="أ", position=0
        )
        second = ProductImage.objects.create(
            product=product, legacy_path="/static/b.webp", alt="ب", position=1
        )
        before = selectors.get_product_detail(product.slug)["product"]["images"]
        assert [image["path"] for image in before] == ["/static/a.webp", "/static/b.webp"]

        first.position, second.position = 1, 0
        first.save(update_fields=["position"])
        second.save(update_fields=["position"])

        after = selectors.get_product_detail(product.slug)["product"]["images"]
        assert [image["path"] for image in after] == ["/static/b.webp", "/static/a.webp"]

    def test_reordering_variants_changes_the_finish_order(
        self, product, variant, second_variant
    ):
        before = selectors.get_product_detail(product.slug)["product"]["finishes"]
        assert [finish["id"] for finish in before] == [
            variant.finish_id,
            second_variant.finish_id,
        ]

        variant.position, second_variant.position = 1, 0
        variant.save(update_fields=["position"])
        second_variant.save(update_fields=["position"])

        after = selectors.get_product_detail(product.slug)["product"]["finishes"]
        assert [finish["id"] for finish in after] == [
            second_variant.finish_id,
            variant.finish_id,
        ]

    @pytest.mark.parametrize("inline_class", [ProductImageInline, ProductVariantInline])
    def test_staff_can_edit_the_position_on_the_product_form(
        self, staff_request, inline_class
    ):
        inline = inline_class(Product, django_admin.site)

        formset = inline.get_formset(staff_request)

        assert "position" in formset.form.base_fields, (
            f"{inline_class.__name__} does not let staff reorder its rows"
        )
        assert not formset.form.base_fields["position"].disabled


# ---------------------------------------------------------------------------
# Price ownership
# ---------------------------------------------------------------------------


class TestPriceOwnership:
    """Price belongs to the variant; the product only derives a display price,
    and ``compareAtPrice`` is optional but must exceed the price when present
    (FR-017).

    Deriving rather than storing is what makes per-finish pricing possible
    without a schema change, and what stops a product-level price drifting away
    from the price a cart line is actually built from.
    """

    def test_the_product_table_has_no_price_column(self):
        assert "price" not in {field.name for field in Product._meta.get_fields()}
        assert "price" in {field.name for field in ProductVariant._meta.get_fields()}

    def test_the_display_price_tracks_the_default_variant(
        self, product, variant, second_variant
    ):
        assert Product.objects.get(pk=product.pk).display_price == Decimal("7490.00")

        variant.price = Decimal("6990.00")
        variant.save(update_fields=["price"])

        assert Product.objects.get(pk=product.pk).display_price == Decimal("6990.00")

        # A non-default finish may be priced apart without moving the headline
        # price — the point of owning price on the variant.
        second_variant.price = Decimal("7990.00")
        second_variant.save(update_fields=["price"])

        assert Product.objects.get(pk=product.pk).display_price == Decimal("6990.00")

    def test_compare_at_price_is_optional(self, product):
        created = ProductVariant.objects.create(
            product=product, sku="ZK-NO-COMPARE", price=Decimal("7490.00")
        )

        assert created.compare_at_price is None
        assert Product.objects.get(pk=product.pk).compare_at_price is None

    @pytest.mark.parametrize("compare_at", [Decimal("7490.00"), Decimal("6000.00")])
    def test_the_database_refuses_a_compare_at_price_that_is_not_above_price(
        self, product, compare_at
    ):
        """A strike-through at or below the price advertises a fake discount."""
        with pytest.raises(IntegrityError), transaction.atomic():
            ProductVariant.objects.create(
                product=product,
                sku="ZK-BAD-COMPARE",
                price=Decimal("7490.00"),
                compare_at_price=compare_at,
            )

        assert not ProductVariant.objects.filter(sku="ZK-BAD-COMPARE").exists()

    def test_a_higher_compare_at_price_is_accepted_and_exposed(self, product):
        ProductVariant.objects.create(
            product=product,
            sku="ZK-GOOD-COMPARE",
            price=Decimal("7490.00"),
            compare_at_price=Decimal("8990.00"),
            is_default=True,
        )

        assert Product.objects.get(pk=product.pk).compare_at_price == Decimal("8990.00")


# ---------------------------------------------------------------------------
# Merchandising fields
# ---------------------------------------------------------------------------


class TestMerchandisingFields:
    """A product carries its SEO title and description, the feature keys the
    catalogue facets are built from, its instalment message and the two service
    flags (FR-019).

    Each is asserted where it is actually used: SEO on the staff form that owns
    it, feature keys through the facet they drive, and the remaining fields
    through the storefront record the product page renders.
    """

    def test_seo_title_and_description_are_stored_and_staff_editable(
        self, product, staff_request
    ):
        product.seo_title = "قفل زاكي أبيكس برو | ZAKEY"
        product.seo_description = "قفل ذكي بخمس وسائل دخول وشاشة داخلية واضحة."
        product.save(update_fields=["seo_title", "seo_description"])

        stored = Product.objects.get(pk=product.pk)
        assert stored.seo_title == "قفل زاكي أبيكس برو | ZAKEY"
        assert stored.seo_description == "قفل ذكي بخمس وسائل دخول وشاشة داخلية واضحة."

        model_admin = django_admin.site._registry[Product]
        editable = set(model_admin.get_form(staff_request)().fields)
        assert {"seo_title", "seo_description"} <= editable

    def test_feature_keys_drive_the_catalogue_facets(self, product, variant, stock):
        ProductFeature.objects.create(
            product=product, key="fingerprint", label="بصمة سريعة", position=0
        )

        assert {facet["key"] for facet in selectors._filter_features()} == {"fingerprint"}

        matched = selectors.get_catalogue({"feature": ["fingerprint"]})
        assert [item["slug"] for item in matched["products"]] == [product.slug]

        # An unknown key is discarded, not treated as a filter that matches
        # nothing — otherwise a stale bookmark would empty the shop.
        assert selectors.get_catalogue({"feature": ["not-a-feature"]})["totalCount"] == 1

    def test_the_instalment_message_and_service_flags_reach_the_storefront(
        self, product, variant
    ):
        product.instalment_message = "خطط تقسيط حتى 12 شهرًا"
        product.same_day_supported = True
        product.installation_supported = False
        product.save(
            update_fields=[
                "instalment_message",
                "same_day_supported",
                "installation_supported",
            ]
        )

        record = selectors.get_product_detail(product.slug)["product"]

        assert record["instalmentMessage"] == "خطط تقسيط حتى 12 شهرًا"
        assert record["serviceFlags"] == {
            "sameDaySupported": True,
            "installationSupported": False,
        }
