"""Coupon administration (FR-104)."""

from __future__ import annotations

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from apps.core.admin_mixins import AuditedImportExportMixin
from apps.core.resources import CouponResource

from .models import Coupon, CouponRedemption


class CouponRedemptionInline(admin.TabularInline):
    model = CouponRedemption
    extra = 0
    readonly_fields = ("order", "customer", "amount", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False


@admin.register(Coupon)
class CouponAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    resource_classes = (CouponResource,)
    list_display = ("code", "discount_type", "value", "times_used", "usage_limit", "is_active", "is_demo")
    list_filter = ("discount_type", "is_active", "is_demo")
    search_fields = ("code",)
    filter_horizontal = ("products", "categories")
    # Usage is system-maintained (INV-005).
    readonly_fields = ("times_used", "created_at", "updated_at")
    inlines = (CouponRedemptionInline,)


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ("created_at", "coupon", "order", "customer", "amount")
    search_fields = ("coupon__code", "order__number")
    readonly_fields = ("coupon", "order", "customer", "amount", "created_at")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False
