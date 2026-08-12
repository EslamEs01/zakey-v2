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


class OrderLineResource(ExportOnlyResource):
    """Line-level order export.

    ``OrderResource`` exports one row per order, which cannot answer "how many
    of SKU X did we sell". This is the same history at line granularity: still
    export-only, for the same reason.
    """

    class Meta:
        from apps.orders.models import OrderLine

        model = OrderLine
        fields = (
            "id",
            "order__number",
            "order__status",
            "order__placed_at",
            "sku",
            "product_name",
            "variant_label",
            "unit_price",
            "quantity",
            "line_total",
        )


class RefundResource(ExportOnlyResource):
    class Meta:
        from apps.payments.models import Refund

        model = Refund
        fields = (
            "id",
            "payment__order__number",
            "amount",
            "reason",
            "state",
            "actor__email",
            "created_at",
        )


# ---------------------------------------------------------------------------
# Reference and content resources
#
# Everything below is catalogue or configuration rather than financial history,
# so all of it both imports and exports: these are precisely the tables a shop
# populates in bulk from a spreadsheet at launch, and re-exports to hand to a
# translator (FR-104, FR-136).
# ---------------------------------------------------------------------------


class CategoryResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import Category

        model = Category
        import_id_fields = ("slug",)
        fields = (
            "id", "slug", "name", "name_en", "description", "description_en",
            "kind", "kind_en", "parent", "position", "status",
            "seo_title", "seo_title_en", "seo_description", "seo_description_en",
        )
        skip_unchanged = True
        report_skipped = True


class BrandResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import Brand

        model = Brand
        import_id_fields = ("slug",)
        fields = ("id", "slug", "name", "name_en")
        skip_unchanged = True
        report_skipped = True


class CollectionResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import Collection

        model = Collection
        import_id_fields = ("slug",)
        fields = (
            "id", "slug", "name", "name_en", "description", "description_en",
            "promotion_eyebrow", "promotion_eyebrow_en", "position", "status",
        )
        skip_unchanged = True
        report_skipped = True


class ProductFeatureResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import ProductFeature

        model = ProductFeature
        fields = (
            "id", "product", "key", "label", "label_en",
            "description", "description_en", "position",
        )
        skip_unchanged = True
        report_skipped = True


class SpecificationItemResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.catalog.models import SpecificationItem

        model = SpecificationItem
        fields = ("id", "group", "label", "label_en", "value", "value_en", "position")
        skip_unchanged = True
        report_skipped = True


class FAQResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.content.models import FAQ

        model = FAQ
        fields = (
            "id", "legacy_id", "question", "question_en", "answer", "answer_en",
            "page", "position", "is_active",
        )
        skip_unchanged = True
        report_skipped = True


class StaticPageResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.content.models import StaticPage

        model = StaticPage
        import_id_fields = ("slug",)
        fields = (
            "id", "slug", "title", "title_en", "body", "body_en",
            "seo_title", "seo_title_en", "seo_description", "seo_description_en",
            "is_published",
        )
        skip_unchanged = True
        report_skipped = True


class NavigationItemResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.content.models import NavigationItem

        model = NavigationItem
        fields = (
            "id", "label", "label_en", "href", "route_name", "icon",
            "group", "position", "is_active",
        )
        skip_unchanged = True
        report_skipped = True


class GovernorateResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.shipping.models import Governorate

        model = Governorate
        import_id_fields = ("key",)
        fields = ("id", "key", "name", "name_en", "position", "is_active")
        skip_unchanged = True
        report_skipped = True


class ServiceAreaResource(AuditedResourceMixin, resources.ModelResource):
    class Meta:
        from apps.shipping.models import ServiceArea

        model = ServiceArea
        import_id_fields = ("key",)
        fields = (
            "id", "key", "name", "name_en", "governorate",
            "same_day_eligible", "installation_eligible", "is_active",
        )
        skip_unchanged = True
        report_skipped = True


class ShippingRateResource(AuditedResourceMixin, resources.ModelResource):
    """Rates import: this is the table a shop updates when prices change.

    ``is_placeholder`` is exported so a spreadsheet round-trip cannot silently
    promote a development placeholder into an approved commercial price
    (ASM-004).
    """

    class Meta:
        from apps.shipping.models import ShippingRate

        model = ShippingRate
        fields = ("id", "method", "zone", "price", "is_placeholder", "is_active")
        skip_unchanged = True
        report_skipped = True


class ReviewResource(ExportOnlyResource):
    """Customer-written content: exported for moderation review, never imported.

    Importing would mean writing reviews on customers' behalf, which is the one
    thing a review system must not offer (FR-091).
    """

    class Meta:
        from apps.reviews.models import Review

        model = Review
        fields = (
            "id", "product", "author_name", "rating", "title", "body",
            "status", "is_verified_purchase", "created_at",
        )


class CustomerProfileResource(ExportOnlyResource):
    """Export-only, and deliberately without the phone number.

    Full contact detail is gated behind ``accounts.view_full_contact`` in the
    admin (FR-112). An export that carried it would be a way around that check
    for anyone who can reach the export button.
    """

    class Meta:
        from apps.accounts.models import CustomerProfile

        model = CustomerProfile
        fields = (
            "id", "full_name", "user__email", "email_verified",
            "phone_verified", "accepts_marketing", "created_at",
        )


class NewsletterSubscriptionResource(ExportOnlyResource):
    class Meta:
        from apps.content.models import NewsletterSubscription

        model = NewsletterSubscription
        fields = ("id", "email", "source", "confirmed", "created_at")


class ContactMessageResource(ExportOnlyResource):
    class Meta:
        from apps.content.models import ContactMessage

        model = ContactMessage
        fields = ("id", "name", "email", "phone", "subject", "message", "status", "created_at")


class StockMovementResource(ExportOnlyResource):
    """The stock ledger, for reconciliation. Append-only, so never importable."""

    class Meta:
        from apps.inventory.models import StockMovement

        model = StockMovement
        fields = (
            "id", "stock_item__variant__sku", "delta", "reason",
            "on_hand_after", "reserved_after", "actor__email", "created_at",
        )


class AuditLogResource(ExportOnlyResource):
    class Meta:
        from apps.audit.models import AuditLog

        model = AuditLog
        fields = (
            "id", "created_at", "actor__email", "action", "content_type",
            "object_id", "object_repr", "request_id",
        )
