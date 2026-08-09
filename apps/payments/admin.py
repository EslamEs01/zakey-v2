"""Payments administration (FR-105, FR-075, INV-004)."""

from __future__ import annotations

from django.contrib import admin

from import_export.admin import ExportMixin

from apps.core.admin_mixins import AppendOnlyAdmin
from apps.core.resources import PaymentResource

from .models import Payment, PaymentEvent, PaymentMethod, Refund


class PaymentEventInline(admin.TabularInline):
    model = PaymentEvent
    extra = 0
    can_delete = False
    readonly_fields = ("created_at", "event_type", "provider_event_id", "payload_digest", "note")

    def has_add_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False

    def has_change_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("label", "code", "is_active", "is_integrated", "collects_on_delivery", "is_manual", "position")
    list_filter = ("is_active", "is_integrated")
    search_fields = ("code", "label")
    # No provider integration exists; this flag is informational only (FR-071).
    readonly_fields = ("is_integrated",)


@admin.register(Payment)
class PaymentAdmin(ExportMixin, admin.ModelAdmin):
    # Export only, for the same reason orders are (FR-104).
    resource_classes = (PaymentResource,)
    list_display = ("order", "method", "amount", "currency", "state", "captured_at", "recorded_by")
    list_filter = ("state", "method")
    search_fields = ("order__number", "provider_reference")
    date_hierarchy = "created_at"
    # Amount and state change only through validated services (FR-105).
    readonly_fields = ("order", "method", "amount", "currency", "state", "provider_reference",
                       "idempotency_key", "captured_at", "recorded_by", "created_at", "updated_at")
    inlines = (PaymentEventInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "method", "recorded_by")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False


@admin.register(PaymentEvent)
class PaymentEventAdmin(AppendOnlyAdmin):
    list_display = ("created_at", "payment", "event_type", "provider_event_id")
    search_fields = ("provider_event_id", "payment__order__number")
    date_hierarchy = "created_at"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("created_at", "payment", "amount", "state", "actor")
    list_filter = ("state",)
    search_fields = ("payment__order__number", "reason")
    date_hierarchy = "created_at"
    readonly_fields = ("payment", "amount", "state", "provider_reference", "actor", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("payment__order", "actor")

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False
