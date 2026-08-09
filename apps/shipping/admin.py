"""Shipping administration (FR-045).

Placeholder rates are surfaced explicitly so nobody mistakes a development
value for an approved commercial price (ASM-004, ASM-005).
"""

from __future__ import annotations

from django.contrib import admin

from .models import (
    Governorate,
    InstallationService,
    ServiceArea,
    ShippingMethod,
    ShippingRate,
    ShippingZone,
)


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "position", "is_active")
    search_fields = ("name", "key")
    list_editable = ("position", "is_active")


@admin.register(ServiceArea)
class ServiceAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "governorate", "same_day_eligible", "installation_eligible", "is_active")
    list_filter = ("governorate", "same_day_eligible", "installation_eligible")
    search_fields = ("name", "key")
    autocomplete_fields = ("governorate",)


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ("name", "position", "is_active")
    filter_horizontal = ("governorates",)


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ("label", "code", "requires_area_eligibility", "free_over_threshold", "position", "is_active")
    search_fields = ("code", "label")


@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ("method", "zone", "price", "placeholder_warning", "is_active")
    list_filter = ("method", "zone", "is_placeholder", "is_active")
    list_editable = ("price", "is_active")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("method", "zone")

    @admin.display(description="حالة السعر", boolean=False)
    def placeholder_warning(self, obj):
        return "قيمة تطويرية غير معتمدة" if obj.is_placeholder else "معتمد"


@admin.register(InstallationService)
class InstallationServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "fee", "placeholder_warning", "is_active")
    filter_horizontal = ("governorates",)

    @admin.display(description="حالة الرسوم")
    def placeholder_warning(self, obj):
        return "قيمة تطويرية غير معتمدة" if obj.is_placeholder else "معتمد"
