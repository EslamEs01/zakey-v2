"""Catalogue administration (FR-104, FR-108, FR-109)."""

from __future__ import annotations

from django.contrib import admin

from import_export.admin import ImportExportModelAdmin

from apps.core.admin_mixins import ArchivableAdmin, AuditedImportExportMixin
from apps.core.resources import ProductResource, ProductVariantResource

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
    fields = ("sku", "finish_label", "swatch_hex", "price", "compare_at_price", "position", "is_default", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "legacy_path", "alt", "position")
    ordering = ("position",)


class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1
    fields = ("key", "label", "description", "position")


class SpecificationGroupInline(admin.TabularInline):
    model = SpecificationGroup
    extra = 0
    fields = ("label", "position")


class ProductDocumentInline(admin.TabularInline):
    model = ProductDocument
    extra = 0
    fields = ("label", "file", "legacy_path", "file_format", "position")


class ProductRelationInline(admin.TabularInline):
    model = ProductRelation
    fk_name = "from_product"
    extra = 0
    autocomplete_fields = ("to_product",)


@admin.register(Product)
class ProductAdmin(AuditedImportExportMixin, ArchivableAdmin, ImportExportModelAdmin):
    resource_classes = (ProductResource,)
    list_display = ("name", "slug", "category", "display_price", "availability", "status", "updated_at")
    list_filter = ("status", "category", "same_day_supported", "installation_supported")
    search_fields = ("name", "slug", "short_description", "variants__sku")
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
        ("التصنيف", {"fields": ("category", "brand", "badge", "position")}),
        ("الخدمات", {"fields": ("same_day_supported", "installation_supported", "instalment_message")}),
        ("SEO", {"fields": ("seo_title", "seo_description")}),
        ("النشر", {"fields": ("status", "published_at", "archived_at")}),
        ("تقني", {"classes": ("collapse",), "fields": ("legacy_id", "rating_average", "review_count", "created_at", "updated_at")}),
    )

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
class CategoryAdmin(ArchivableAdmin):
    list_display = ("name", "slug", "parent", "position", "status")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Collection)
class CollectionAdmin(ArchivableAdmin):
    list_display = ("name", "slug", "position", "status")
    list_filter = ("status",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (type("CollectionProductInline", (admin.TabularInline,), {
        "model": CollectionProduct, "extra": 1, "autocomplete_fields": ("product",)
    }),)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


admin.site.register(SpecificationItem)
