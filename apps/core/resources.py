"""Import/export resources for the admin (T-1309, FR-104).

The split here is the whole point:

* **Product, ProductVariant, StockItem and Coupon are importable.** They are
  catalogue maintenance — the kind of bulk edit a merchandiser genuinely does
  from a spreadsheet.
* **Orders and payments are export-only.** They are financial history. There is
  no legitimate reason to *write* an order from a spreadsheet, and offering the
  button would be offering a way to forge one. Their resources deliberately
  refuse import rather than merely hiding the tab (FR-104, INV-003).

``django-import-export`` already runs an import inside a transaction and offers
a dry-run confirmation page before committing. What this module adds is the
audit trail: a bulk edit that leaves no evidence of who made it is exactly the
change nobody can explain afterwards.
"""

from __future__ import annotations

from import_export import resources
from import_export.exceptions import ImportError as ImportNotAllowed


class AuditedResourceMixin:
    """Write one audit row per imported record (FR-113)."""

    def after_save_instance(self, instance, row, **kwargs):  # noqa: D102
        super().after_save_instance(instance, row, **kwargs)
        if kwargs.get("dry_run"):
            # A preview must not leave evidence of a change that never happened.
            return
        from apps.audit.models import AuditAction
        from apps.audit.services import record_audit

        record_audit(
            getattr(self, "_actor", None),
            AuditAction.UPDATE,
            instance,
            {"source": "admin_import", "model": instance._meta.label},
        )


class ExportOnlyResource(resources.ModelResource):
    """A resource that will export but never import.

    Refusing in ``before_import`` rather than only hiding the UI means a crafted
    POST straight to the import endpoint is refused too.
    """

    def before_import(self, dataset, **kwargs):  # noqa: D102
        raise ImportNotAllowed(
            "لا يمكن استيراد الطلبات أو المدفوعات؛ التصدير فقط (FR-104)."
        )

    def skip_row(self, instance, original, row, import_validation_errors=None):  # noqa: D102
        return True


# ---------------------------------------------------------------------------
# Importable catalogue resources
# ---------------------------------------------------------------------------


class ProductResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import Product

        model = Product
        import_id_fields = ("slug",)
        fields = (
            "id",
            "slug",
            "name",
            "short_description",
            "category",
            "brand",
            "badge",
            "position",
            "status",
            "same_day_supported",
            "installation_supported",
            "seo_title",
            "seo_description",
        )
        skip_unchanged = True
        report_skipped = True


class ProductVariantResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import ProductVariant

        model = ProductVariant
        import_id_fields = ("sku",)
        fields = (
            "id",
            "sku",
            "product",
            "finish_id",
            "finish_label",
            "swatch_hex",
            "price",
            "compare_at_price",
            "position",
            "is_default",
            "is_active",
        )
        skip_unchanged = True
        report_skipped = True


class StockItemResource(AuditedResourceMixin, resources.ModelResource):
    """Thresholds only — never levels.

    ``on_hand`` and ``reserved`` are excluded on purpose. Stock moves through
    the ledger so every change is attributable (FR-021, FR-105); letting a
    spreadsheet overwrite a level would break that and silently orphan the
    movement history.
    """

    class Meta:
        from apps.inventory.models import StockItem

        model = StockItem
        import_id_fields = ("variant",)
        fields = ("id", "variant", "low_stock_threshold")
        skip_unchanged = True
        report_skipped = True


class CouponResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.promotions.models import Coupon

        model = Coupon
        import_id_fields = ("code",)
        fields = (
            "id",
            "code",
            "description",
            "discount_type",
            "value",
            "max_discount",
            "starts_at",
            "ends_at",
            "usage_limit",
            "per_customer_limit",
            "minimum_subtotal",
            "is_active",
        )
        # times_used is system-maintained; importing it would rewrite history.
        skip_unchanged = True
        report_skipped = True


# ---------------------------------------------------------------------------
# Export-only financial resources
# ---------------------------------------------------------------------------


class OrderResource(ExportOnlyResource):
    class Meta:
        from apps.orders.models import Order

        model = Order
        fields = (
            "id",
            "number",
            "status",
            "payment_status",
            "fulfillment_status",
            "email",
            "phone",
            "subtotal",
            "grand_total",
            "placed_at",
        )


class PaymentResource(ExportOnlyResource):
    class Meta:
        from apps.payments.models import Payment

        model = Payment
        fields = ("id", "order", "method", "state", "amount", "currency", "created_at")
