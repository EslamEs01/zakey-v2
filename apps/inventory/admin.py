"""Inventory administration (FR-105, FR-021, FR-022).

Stock levels are never typed in. The only way to change them is the
``adjust_stock`` action, which demands a delta and a reason and writes a ledger
row — so every movement is attributable.
"""

from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render

from import_export.admin import ImportExportModelAdmin

from apps.core.admin_mixins import AppendOnlyAdmin, AuditedImportExportMixin
from apps.core.resources import StockItemResource

from .models import MovementReason, StockItem, StockMovement, StockReservation
from .services import adjust


class StockAdjustForm(forms.Form):
    delta = forms.IntegerField(label="التغيير (+/-)")
    reason = forms.ChoiceField(label="السبب", choices=MovementReason.choices)
    note = forms.CharField(label="ملاحظة", required=False, max_length=255)


@admin.register(StockItem)
class StockItemAdmin(AuditedImportExportMixin, ImportExportModelAdmin):
    # Thresholds import; levels never do — they move through the ledger.
    resource_classes = (StockItemResource,)
    list_display = ("sku", "product", "on_hand", "reserved", "available_display", "state_badge")
    search_fields = ("variant__sku", "variant__product__name")
    # Levels are read-only: use the action (FR-105).
    readonly_fields = ("variant", "on_hand", "reserved", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("variant__product")

    @admin.display(description="SKU")
    def sku(self, obj):
        return obj.variant.sku

    @admin.display(description="المنتج")
    def product(self, obj):
        return obj.variant.product.name

    @admin.display(description="المتاح")
    def available_display(self, obj):
        return obj.available

    @admin.display(description="الحالة")
    def state_badge(self, obj):
        if obj.is_out_of_stock:
            return "نفد"
        if obj.is_low_stock:
            return "منخفض"
        return "متاح"

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False

    @admin.action(description="تسوية المخزون (تتطلب سببًا)")
    def adjust_stock(self, request, queryset):
        if "apply" in request.POST:
            form = StockAdjustForm(request.POST)
            if form.is_valid():
                succeeded, failed = 0, []
                for item in queryset.select_related("variant"):
                    try:
                        adjust(
                            item.variant,
                            form.cleaned_data["delta"],
                            form.cleaned_data["reason"],
                            actor=request.user,
                            note=form.cleaned_data["note"],
                        )
                        succeeded += 1
                    except ValidationError as exc:
                        failed.append(f"{item.variant.sku}: {exc.messages[0]}")
                if succeeded:
                    self.message_user(request, f"تمت تسوية {succeeded} رصيدًا.", messages.SUCCESS)
                for problem in failed:
                    self.message_user(request, problem, messages.ERROR)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = StockAdjustForm()
        return render(
            request,
            "admin/stock_adjust.html",
            {"items": queryset, "form": form, "title": "تسوية المخزون"},
        )

    actions = ("adjust_stock",)


@admin.register(StockMovement)
class StockMovementAdmin(AppendOnlyAdmin):
    list_display = ("created_at", "sku", "delta", "reason", "on_hand_after", "reserved_after", "actor")
    list_filter = ("reason",)
    search_fields = ("stock_item__variant__sku",)
    date_hierarchy = "created_at"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("stock_item__variant", "actor")

    @admin.display(description="SKU")
    def sku(self, obj):
        return obj.stock_item.variant.sku


@admin.register(StockReservation)
class StockReservationAdmin(admin.ModelAdmin):
    list_display = ("created_at", "sku", "quantity", "state", "expires_at", "order")
    list_filter = ("state",)
    search_fields = ("stock_item__variant__sku", "order__number")
    readonly_fields = ("stock_item", "order", "quantity", "state", "expires_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("stock_item__variant", "order")

    @admin.display(description="SKU")
    def sku(self, obj):
        return obj.stock_item.variant.sku

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False
