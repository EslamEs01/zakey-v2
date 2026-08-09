"""Admin import/export (T-1309, FR-104, FR-113).

The rule that matters: **catalogue data imports, financial history does not.**
A spreadsheet is a fine way to reprice a hundred products. It is not a way to
create an order, and offering that button would be offering a way to forge one.

The refusal is tested at the resource level, not only at the UI level, because
hiding a tab is not authorisation.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
import tablib
from django.contrib.admin.sites import site
from django.urls import reverse

from apps.audit.models import AuditLog
from apps.catalog.models import Product, ProductVariant
from apps.core import resources
from apps.inventory.models import StockItem
from apps.orders.models import Order
from apps.payments.models import Payment
from apps.promotions.models import Coupon

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# What may be imported, and what may not
# ---------------------------------------------------------------------------


IMPORTABLE = {
    Product: resources.ProductResource,
    ProductVariant: resources.ProductVariantResource,
    StockItem: resources.StockItemResource,
    Coupon: resources.CouponResource,
}

EXPORT_ONLY = {
    Order: resources.OrderResource,
    Payment: resources.PaymentResource,
}


class TestImportSurface:
    @pytest.mark.parametrize("model", sorted(IMPORTABLE, key=lambda m: m.__name__))
    def test_the_four_catalogue_models_are_importable(self, model):
        from import_export.admin import ImportMixin

        assert isinstance(site._registry[model], ImportMixin), (
            f"{model.__name__} should be importable per FR-104"
        )

    @pytest.mark.parametrize("model", sorted(EXPORT_ONLY, key=lambda m: m.__name__))
    def test_financial_models_are_not_importable(self, model):
        from import_export.admin import ImportMixin

        assert not isinstance(site._registry[model], ImportMixin), (
            f"{model.__name__} must be export-only (FR-104)"
        )

    @pytest.mark.parametrize("model", sorted(EXPORT_ONLY, key=lambda m: m.__name__))
    def test_financial_models_are_still_exportable(self, model):
        from import_export.admin import ExportMixin

        assert isinstance(site._registry[model], ExportMixin)

    @pytest.mark.parametrize(
        "resource_class", [resources.OrderResource, resources.PaymentResource]
    )
    def test_the_resource_itself_refuses_an_import(self, resource_class):
        """Not merely hidden in the UI — refused at the resource.

        A crafted POST to the import endpoint has to fail too.
        """
        from import_export.exceptions import ImportError as ImportNotAllowed

        dataset = tablib.Dataset(headers=["id", "number"])
        dataset.append([1, "ZK-FORGED"])

        with pytest.raises(ImportNotAllowed):
            resource_class().import_data(dataset, raise_errors=True)

    def test_no_order_is_created_by_an_attempted_import(self):
        dataset = tablib.Dataset(headers=["id", "number"])
        dataset.append([1, "ZK-FORGED"])

        try:
            resources.OrderResource().import_data(dataset, raise_errors=False)
        except Exception:
            pass

        assert not Order.objects.filter(number="ZK-FORGED").exists()


# ---------------------------------------------------------------------------
# Importing works, previews first, and is transactional
# ---------------------------------------------------------------------------


class TestProductImport:
    def _dataset(self, product, new_name="اسم محدّث"):
        return tablib.Dataset(
            [product.slug, new_name],
            headers=["slug", "name"],
        )

    def test_a_dry_run_changes_nothing(self, product):
        original = product.name

        result = resources.ProductResource().import_data(
            self._dataset(product), dry_run=True
        )

        product.refresh_from_db()
        assert not result.has_errors()
        assert product.name == original, "the preview committed the change"

    def test_a_real_run_applies_the_change(self, product):
        resources.ProductResource().import_data(self._dataset(product), dry_run=False)

        product.refresh_from_db()
        assert product.name == "اسم محدّث"

    def test_a_dry_run_writes_no_audit_row(self, product):
        before = AuditLog.objects.count()

        resources.ProductResource().import_data(self._dataset(product), dry_run=True)

        assert AuditLog.objects.count() == before, (
            "a preview left evidence of a change that never happened"
        )

    def test_a_real_import_is_audited(self, product):
        resources.ProductResource().import_data(self._dataset(product), dry_run=False)

        entry = AuditLog.objects.filter(changes__source="admin_import").latest("id")
        assert entry.changes["model"] == "catalog.Product"

    def test_a_failed_row_rolls_the_whole_import_back(self, product, category):
        """Transactional: a partial catalogue import is worse than none."""
        dataset = tablib.Dataset(headers=["slug", "name", "position"])
        dataset.append([product.slug, "اسم صالح", "0"])
        dataset.append(["another-slug", "اسم آخر", "not-an-integer"])

        resources.ProductResource().import_data(
            dataset, dry_run=False, raise_errors=False, use_transactions=True
        )

        product.refresh_from_db()
        assert product.name != "اسم صالح", "a broken row still committed its neighbours"


class TestStockImportIsThresholdsOnly:
    def test_levels_are_not_importable_fields(self):
        """Stock moves through the ledger, never through a spreadsheet."""
        fields = set(resources.StockItemResource().get_export_headers())

        assert "on_hand" not in fields
        assert "reserved" not in fields

    def test_the_threshold_is_importable(self, variant, stock):
        dataset = tablib.Dataset(
            [str(variant.pk), "7"], headers=["variant", "low_stock_threshold"]
        )

        resources.StockItemResource().import_data(dataset, dry_run=False)

        stock.refresh_from_db()
        assert stock.low_stock_threshold == 7

    def test_an_import_cannot_change_a_level(self, variant, stock):
        original = stock.on_hand
        dataset = tablib.Dataset(
            [str(variant.pk), "9999"], headers=["variant", "on_hand"]
        )

        resources.StockItemResource().import_data(dataset, dry_run=False)

        stock.refresh_from_db()
        assert stock.on_hand == original, "a spreadsheet rewrote a stock level"


class TestCouponImport:
    def test_times_used_is_not_importable(self):
        """A system-maintained counter must not be rewritten from a file."""
        assert "times_used" not in set(resources.CouponResource().get_export_headers())

    def test_a_coupon_can_be_created_by_import(self, db):
        dataset = tablib.Dataset(
            ["WELCOME10", "percentage", "10.00"],
            headers=["code", "discount_type", "value"],
        )

        resources.CouponResource().import_data(dataset, dry_run=False)

        assert Coupon.objects.filter(code="WELCOME10").exists()


# ---------------------------------------------------------------------------
# Export still works through the admin
# ---------------------------------------------------------------------------


class TestExportThroughTheAdmin:
    @pytest.fixture
    def staff_client(self, client, db):
        from apps.accounts.models import User

        staff = User.objects.create_superuser(
            email="admin@zakey.test", password="Admin!2345"
        )
        client.force_login(staff)
        return client

    def test_the_order_export_page_is_reachable(self, staff_client):
        response = staff_client.get(reverse("admin:orders_order_export"))
        assert response.status_code == 200

    def test_there_is_no_order_import_url(self, staff_client):
        from django.urls import NoReverseMatch

        with pytest.raises(NoReverseMatch):
            reverse("admin:orders_order_import")

    def test_the_product_import_page_is_reachable(self, staff_client):
        response = staff_client.get(reverse("admin:catalog_product_import"))
        assert response.status_code == 200

    def test_an_exported_order_carries_its_financial_columns(self, db):
        Order.objects.create(
            number="ZK-EXP-1",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="key-exp-1",
            subtotal=Decimal("7490.00"),
            grand_total=Decimal("7490.00"),
        )

        exported = resources.OrderResource().export()

        assert "grand_total" in exported.headers
        assert "ZK-EXP-1" in str(exported.export("csv"))
