"""Site settings administration (FR-005)."""

from __future__ import annotations

from django.contrib import admin

from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Singleton: exactly one row, never deleted."""

    fieldsets = (
        ("التجارة", {
            "fields": ("vat_rate", "free_shipping_threshold", "currency_code",
                       "currency_label", "currency_decimal_places"),
            "description": "أسعار الكتالوج شاملة الضريبة؛ تُستخرج الضريبة ولا تُضاف إليها.",
        }),
        ("الطلبات والسلة", {"fields": ("order_number_prefix", "max_line_quantity", "cart_ttl_days")}),
        ("المخزون", {"fields": ("reservation_ttl_minutes", "low_stock_threshold")}),
        ("تنويهات", {"fields": ("prototype_notice",)}),
    )
    readonly_fields = ("created_at", "updated_at")

    def has_add_permission(self, request) -> bool:
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False
