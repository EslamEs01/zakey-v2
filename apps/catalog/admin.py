"""Catalogue administration (FR-104, FR-108, FR-109)."""

from __future__ import annotations

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from apps.core.admin_mixins import ArchivableAdmin, AuditedImportExportMixin
from apps.core.resources import (
    BrandResource,
    CategoryResource,
    CollectionResource,
    ProductFeatureResource,
    ProductResource,
    ProductVariantResource,
    SpecificationItemResource,
)

from .models import (
    Brand,
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductDocument,
    ProductFeature,
    ProductImage,
    ProductRelation,
    ProductVariant,
    SpecificationGroup,
    SpecificationItem,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("sku", "finish_id", "finish_label", "finish_label_en", "swatch_hex", "price", "compare_at_price", "position", "is_default", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "legacy_path", "alt", "alt_en", "position")
    ordering = ("position",)


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    fields = ("key", "label", "label_en", "description", "description_en", "position")


class SpecificationGroupInline(admin.TabularInline):
    model = SpecificationGroup
    extra = 0
    fields = ("label", "label_en", "position")


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 0
    fields = ("label", "label_en", "file", "legacy_path", "file_format", "notice", "notice_en", "position")


class ProductRelationInline(admin.TabularInline):
    model = ProductRelation
    fk_name = "from_product"
    extra = 0
    autocomplete_fields = ("to_product",)


@admin.register(Product)
class ProductAdmin(AuditedImportExportMixin, ArchivableAdmin, ImportExportModelAdmin):
    resource_classes = (ProductResource,)
    list_display = ("name", "slug", "category", "display_price", "availability", "status", "english_ready", "updated_at")
    list_filter = ("status", "category", "same_day_supported", "installation_supported")
    search_fields = ("name", "name_en", "slug", "short_description", "variants__sku")
    ordering = ("-updated_at",)
    date_hierarchy = "published_at"
    prepopulated_fields = {"slug": ("name",)}
    autocomplete_fields = ("category", "brand")
    # System-maintained aggregates are never hand-edited (FR-094).
    readonly_fields = ("rating_average", "review_count", "created_at", "updated_at", "legacy_id")
    inlines = (
        ProductVariantInline,
        ProductImageInline,
        ProductFeatureInline,
        SpecificationGroupInline,
        ProductDocumentInline,
        ProductRelationInline,
    )
    fieldsets = (
        ("الهوية", {"fields": ("name", "slug", "short_description", "description")}),
        # English copy is grouped rather than interleaved so the Arabic form
        # stays the short one staff fill in every day; the translation is a
        # separate pass, often by a different person (FR-136).
        ("النسخة الإنجليزية", {
            "classes": ("collapse",),
            "fields": ("name_en", "short_description_en", "description_en",
                       "badge_en", "instalment_message_en",
                       "seo_title_en", "seo_description_en"),
            "description": "تُترك فارغة لعرض النص العربي لزوار الإنجليزية.",
        }),
        ("التصنيف", {"fields": ("category", "brand", "badge", "position")}),
        ("الخدمات", {"fields": ("same_day_supported", "installation_supported", "instalment_message")}),
        ("SEO", {"fields": ("seo_title", "seo_description")}),
        ("النشر", {"fields": ("status", "published_at", "archived_at")}),
        ("تقني", {"classes": ("collapse",), "fields": ("legacy_id", "rating_average", "review_count", "created_at", "updated_at")}),
    )

    change_form_template = "admin/catalog/product_change_form.html"

    def get_urls(self):
        # Prepended: the stock ``<path:object_id>/`` change route would
        # otherwise match ``<id>/bulk-images/`` first and 404 on the pk.
        from .admin_uploads import bulk_upload_urls

        return bulk_upload_urls(self) + super().get_urls()

    def get_queryset(self, request):
        # Bounded query for the changelist (FR-106, NFR-003).
        return (
            super()
            .get_queryset(request)
            .select_related("category", "brand")
            .prefetch_related("variants__stock_item", "images")
        )

    @admin.display(description="السعر")
    def display_price(self, obj):
        return obj.display_price

    @admin.display(description="التوفر")
    def availability(self, obj):
        return obj.availability

    @admin.display(description="الإنجليزية", boolean=True)
    def english_ready(self, obj):
        """Does this product read as English to an English visitor? (FR-136)

        Shown in the changelist because the failure is otherwise invisible: an
        untranslated product does not error, it silently serves Arabic on an
        English page, and nobody notices until a customer does.
        """
        return obj.translation_complete


@admin.register(ProductVariant)
class ProductVariantAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (ProductVariantResource,)
    list_display = ("sku", "product", "finish_label", "price", "is_default", "is_active")
    list_filter = ("is_active", "is_default")
    search_fields = ("sku", "product__name")
    autocomplete_fields = ("product",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("product")


@admin.register(Category)
class CategoryAdmin(AuditedImportExportMixin, ArchivableAdmin, ImportExportModelAdmin):
    resource_classes = (CategoryResource,)
    list_display = ("name", "slug", "parent", "position", "status")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Collection)
class CollectionAdmin(AuditedImportExportMixin, ArchivableAdmin, ImportExportModelAdmin):
    resource_classes = (CollectionResource,)
    list_display = ("name", "slug", "position", "status")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (type("CollectionProductInline", (admin.TabularInline,), {
        "model": CollectionProduct, "extra": 1, "autocomplete_fields": ("product",)
    }),)


@admin.register(Brand)
class BrandAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (BrandResource,)
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SpecificationItem)
class SpecificationItemAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (SpecificationItemResource,)
    list_display = ("label", "value", "group", "position")
    search_fields = ("label", "label_en", "value", "value_en")
    autocomplete_fields = ("group",)


@admin.register(ProductFeature)
class ProductFeatureAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (ProductFeatureResource,)
    list_display = ("label", "key", "product", "position")
    list_filter = ("key",)
    search_fields = ("label", "label_en", "key", "product__name")
    autocomplete_fields = ("product",)


@admin.register(SpecificationGroup)
class SpecificationGroupAdmin(admin.ModelAdmin):
    list_display = ("label", "product", "position")
    search_fields = ("label", "label_en", "product__name")
    autocomplete_fields = ("product",)
