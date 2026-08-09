"""Archive-not-delete policy (T-0510, FR-014, FR-109, FR-067).

The rule this file defends: **once history points at a catalogue record, that
record can never be hard-deleted.** It can only be archived, which is a status
change, so every foreign key an order resolves through stays intact.

The interesting cases are the ones where the guard could quietly fail:

* a product whose variants carry no stock row (nothing else would PROTECT it);
* a bulk delete, which bypasses ``Model.delete()`` entirely;
* a cascade, where deleting the *parent* is what reaches the protected child.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db.models.deletion import ProtectedError

from apps.audit.models import AuditAction, AuditLog
from apps.catalog import services
from apps.catalog.models import Category, Collection, Product, ProductVariant
from apps.core.models import PublicationStatus
from apps.orders.models import Order, OrderLine

pytestmark = pytest.mark.django_db


def make_order(number: str = "ZK-ARCH-1") -> Order:
    return Order.objects.create(
        number=number,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=f"key-{number}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


def order_line_for(variant, number: str = "ZK-ARCH-1") -> OrderLine:
    """A purchased line pointing at ``variant`` — this is what makes it history."""
    return OrderLine.objects.create(
        order=make_order(number),
        variant=variant,
        product_name=variant.product.name,
        product_slug=variant.product.slug,
        variant_label=variant.finish_label,
        sku=variant.sku,
        unit_price=variant.price,
        quantity=1,
        line_total=variant.price,
    )


# ---------------------------------------------------------------------------
# Deletion is blocked once an order references the record (FR-014, FR-109)
# ---------------------------------------------------------------------------


class TestOrderedRecordsCannotBeDeleted:
    def test_deleting_an_ordered_product_is_blocked(self, product, variant):
        """The literal T-0510 acceptance criterion."""
        order_line_for(variant)

        with pytest.raises(ValidationError) as caught:
            services.delete_product(product)

        assert "أرشفته" in str(caught.value), "the refusal must offer archiving instead"
        assert Product.objects.filter(pk=product.pk).exists()

    def test_the_block_does_not_depend_on_a_stock_row(self, product, variant):
        """The case that would slip through an inventory-only guard.

        ``StockItem.variant`` is PROTECT, so a variant that happens to carry
        stock is incidentally protected. A variant with **no** stock row has no
        such accidental shield — only a real order-history guard stops it.
        """
        assert not hasattr(variant, "stock_item") or variant.stock_item is None
        order_line_for(variant)

        with pytest.raises(ValidationError):
            services.delete_product(product)

        assert Product.objects.filter(pk=product.pk).exists()

    def test_deleting_the_variant_directly_is_blocked(self, product, variant):
        order_line_for(variant)

        with pytest.raises(ProtectedError):
            variant.delete()

        assert ProductVariant.objects.filter(pk=variant.pk).exists()

    def test_a_queryset_delete_cannot_bypass_the_guard(self, product, variant):
        """``QuerySet.delete()`` never calls ``Model.delete()``.

        If the only guard were application code, this is the call that would
        walk straight past it. PROTECT is enforced by the database instead.
        """
        order_line_for(variant)

        with pytest.raises(ProtectedError):
            Product.objects.filter(pk=product.pk).delete()

        assert Product.objects.filter(pk=product.pk).exists()

    def test_the_order_line_keeps_resolving_its_variant(self, product, variant):
        """INV-003: history must not be silently hollowed out.

        A SET_NULL here would let the delete succeed and merely blank the
        reference — the order would survive but stop pointing at what was sold.
        """
        line = order_line_for(variant)

        with pytest.raises(ValidationError):
            services.delete_product(product)

        line.refresh_from_db()
        assert line.variant_id == variant.pk


# ---------------------------------------------------------------------------
# Deletion is still allowed while nothing historical points at the record
# ---------------------------------------------------------------------------


class TestUnreferencedRecordsRemainDeletable:
    def test_a_product_with_no_history_can_be_deleted(self, product, variant):
        services.delete_product(product)
        assert not Product.objects.filter(pk=product.pk).exists()

    def test_deleting_a_product_writes_an_audit_row(self, product, variant):
        services.delete_product(product)

        entry = AuditLog.objects.filter(action=AuditAction.DELETE).latest("id")
        assert entry.object_repr
        assert entry.changes["model"] == "catalog.Product"

    def test_a_refused_delete_leaves_no_audit_row(self, product, variant):
        """A rolled-back delete must not look like a delete that happened."""
        order_line_for(variant)
        before = AuditLog.objects.filter(action=AuditAction.DELETE).count()

        with pytest.raises(ValidationError):
            services.delete_product(product)

        assert AuditLog.objects.filter(action=AuditAction.DELETE).count() == before


# ---------------------------------------------------------------------------
# Archiving works on everything, always (FR-014)
# ---------------------------------------------------------------------------


class TestArchiving:
    def test_archiving_an_ordered_product_is_allowed(self, product, variant):
        order_line_for(variant)

        services.archive(product)

        product.refresh_from_db()
        assert product.status == PublicationStatus.ARCHIVED
        assert product.archived_at is not None

    def test_archiving_preserves_every_history_reference(self, product, variant):
        line = order_line_for(variant)

        services.archive(product)

        line.refresh_from_db()
        assert line.variant_id == variant.pk
        assert line.product_name == product.name

    def test_archiving_is_idempotent(self, product):
        services.archive(product)
        first = Product.objects.get(pk=product.pk).archived_at

        services.archive(product)

        assert Product.objects.get(pk=product.pk).archived_at == first

    def test_archiving_writes_an_audit_row(self, product):
        services.archive(product)

        entry = AuditLog.objects.filter(action=AuditAction.ARCHIVE).latest("id")
        assert entry.changes["status"]["to"] == PublicationStatus.ARCHIVED

    @pytest.mark.parametrize("model_name", ["Category", "Collection", "Product"])
    def test_every_publishable_entity_is_archivable(self, model_name, category, product):
        assert model_name in {m.__name__ for m in services.archivable_models()}

    def test_categories_and_collections_archive_too(self, category):
        collection = Collection.objects.create(slug="new", name="الجديد")

        services.archive(category)
        services.archive(collection)

        assert Category.objects.get(pk=category.pk).status == PublicationStatus.ARCHIVED
        assert Collection.objects.get(pk=collection.pk).status == PublicationStatus.ARCHIVED

    def test_a_non_publishable_record_is_refused(self, variant):
        """Variants have no lifecycle column; archiving one is a programming error."""
        with pytest.raises(ValidationError):
            services.archive(variant)


# ---------------------------------------------------------------------------
# Restoration (FR-014)
# ---------------------------------------------------------------------------


class TestRestoration:
    def test_restoring_returns_a_draft_not_a_published_record(self, product):
        """Un-archiving must never silently re-expose a product to customers."""
        assert product.status == PublicationStatus.PUBLISHED
        services.archive(product)

        services.restore(product)

        product.refresh_from_db()
        assert product.status == PublicationStatus.DRAFT
        assert product.archived_at is None

    def test_restoring_a_live_record_is_refused(self, product):
        with pytest.raises(ValidationError):
            services.restore(product)

    def test_restoring_writes_an_audit_row(self, product):
        services.archive(product)
        services.restore(product)

        entry = AuditLog.objects.filter(action=AuditAction.STATUS_CHANGE).latest("id")
        assert entry.changes["status"]["to"] == PublicationStatus.DRAFT


# ---------------------------------------------------------------------------
# Bulk operations audit each record rather than issuing one silent UPDATE
# ---------------------------------------------------------------------------


class TestBulkOperations:
    def test_bulk_archive_covers_every_record(self, product, category):
        second = Product.objects.create(
            slug="zakey-lite", name="قفل زاكي لايت", category=category
        )

        count = services.bulk_archive(Product.objects.filter(pk__in=[product.pk, second.pk]))

        assert count == 2
        assert Product.objects.archived().count() == 2

    def test_bulk_archive_audits_each_record_separately(self, product, category):
        second = Product.objects.create(
            slug="zakey-lite", name="قفل زاكي لايت", category=category
        )
        before = AuditLog.objects.filter(action=AuditAction.ARCHIVE).count()

        services.bulk_archive(Product.objects.filter(pk__in=[product.pk, second.pk]))

        after = AuditLog.objects.filter(action=AuditAction.ARCHIVE).count()
        assert after - before == 2, "a raw UPDATE would have left one row or none"

    def test_bulk_restore_only_touches_archived_records(self, product, category):
        live = Product.objects.create(
            slug="zakey-lite", name="قفل زاكي لايت", category=category
        )
        services.archive(product)

        count = services.bulk_restore(Product.objects.filter(pk__in=[product.pk, live.pk]))

        assert count == 1
        live.refresh_from_db()
        assert live.status == PublicationStatus.DRAFT


# ---------------------------------------------------------------------------
# Default query behaviour: archived records leave the active catalogue
# ---------------------------------------------------------------------------


class TestDefaultQueryBehaviour:
    def test_archived_products_leave_active_and_published(self, product):
        services.archive(product)

        assert product not in Product.objects.active()
        assert product not in Product.objects.published()
        assert product in Product.objects.archived()

    def test_active_still_includes_drafts(self, product):
        product.status = PublicationStatus.DRAFT
        product.save(update_fields=["status"])

        assert product in Product.objects.active()
        assert product not in Product.objects.published()

    def test_archived_records_stay_visible_to_staff(self, product):
        """Archiving hides a record from customers, not from the admin."""
        services.archive(product)

        assert Product.objects.filter(pk=product.pk).exists()
        assert Product.objects.archived().filter(pk=product.pk).exists()

    @pytest.mark.parametrize("manager_owner", [Category, Collection, Product])
    def test_every_archivable_model_answers_the_same_questions(self, manager_owner):
        for name in ("active", "published", "archived"):
            assert hasattr(manager_owner.objects, name), (
                f"{manager_owner.__name__}.objects is missing .{name}()"
            )


# ---------------------------------------------------------------------------
# The storefront never serves an archived record (FR-013, FR-067)
# ---------------------------------------------------------------------------


class TestStorefrontExcludesArchived:
    def test_an_archived_product_disappears_from_the_shop(self, storefront):
        from django.urls import reverse

        target = Product.objects.published().first()
        services.archive(target)

        body = storefront.get(reverse("storefront:shop")).content.decode()

        assert target.name not in body

    def test_an_archived_product_detail_page_is_not_served(self, storefront):
        from django.urls import reverse

        target = Product.objects.published().first()
        services.archive(target)

        response = storefront.get(
            reverse("storefront:product", kwargs={"slug": target.slug})
        )

        assert response.status_code == 404

    def test_an_archived_category_disappears_from_navigation(self, storefront):
        from django.urls import reverse

        target = Category.objects.published().first()
        services.archive(target)

        body = storefront.get(reverse("storefront:shop")).content.decode()

        # Scoped to the category radio group: the feature checkboxes reuse some
        # of the same slugs, so a bare value= match would pass for the wrong reason.
        assert f'name="category" value="{target.slug}"' not in body
