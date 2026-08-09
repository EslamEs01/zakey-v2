"""Cart and wishlist administration (read-mostly)."""

from __future__ import annotations

from django.contrib import admin

from .models import Cart, CartLine, Wishlist, WishlistItem


class CartLineInline(admin.TabularInline):
    model = CartLine
    extra = 0
    autocomplete_fields = ("variant",)


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "session_key", "status", "line_count", "updated_at")
    list_filter = ("status",)
    search_fields = ("customer__full_name", "session_key")
    readonly_fields = ("created_at", "updated_at")
    inlines = (CartLineInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("customer").prefetch_related("lines")

    @admin.display(description="عدد الأسطر")
    def line_count(self, obj):
        return obj.lines.count()


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "session_key", "item_count")
    search_fields = ("customer__full_name", "session_key")

    @admin.display(description="عدد المنتجات")
    def item_count(self, obj):
        return obj.items.count()


admin.site.register(WishlistItem)
