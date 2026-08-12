"""Payments administration (FR-105, FR-075, INV-004)."""

from __future__ import annotations

from decimal import Decimal

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render

from import_export.admin import ExportMixin

from apps.core.admin_mixins import AppendOnlyAdmin
from apps.core.resources import PaymentResource, RefundResource

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


class RefundForm(forms.Form):
    """The two things a refund needs and the admin cannot infer."""

    amount = forms.DecimalField(
        label="المبلغ المسترجع", max_digits=12, decimal_places=2,
        min_value=Decimal("0.01"),
    )
    reason = forms.CharField(label="السبب", max_length=255)


@admin.register(Payment)
class PaymentAdmin(ExportMixin, admin.ModelAdmin):
    # Export only, for the same reason orders are (FR-104).
    resource_classes = (PaymentResource,)
    list_display = ("order", "method", "amount", "currency", "state", "refundable", "captured_at", "recorded_by")
    list_filter = ("state", "method")
    search_fields = ("order__number", "provider_reference")
    date_hierarchy = "created_at"
    # Amount and state change only through validated services (FR-105).
    readonly_fields = ("order", "method", "amount", "currency", "state", "provider_reference",
                       "idempotency_key", "captured_at", "recorded_by", "created_at", "updated_at")
    inlines = (PaymentEventInline,)
    actions = ("refund_payments",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order", "method", "recorded_by")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        return False

    @admin.display(description="المتبقي للاسترجاع")
    def refundable(self, obj):
        return obj.refundable_amount

    @admin.action(description="استرجاع مبلغ من الدفعات المختارة")
    def refund_payments(self, request, queryset):
        """Refund through the service, which is the only thing that keeps the
        ledger honest.

        The admin cannot offer a refund as an editable ``Refund`` row: the
        amount has to be checked against what is still captured, the payment
        state has to move with it, and an event and an audit row have to be
        written. ``payments.services.refund`` does all four in one transaction;
        a hand-typed row would do none of them.
        """
        if "apply" in request.POST:
            form = RefundForm(request.POST)
            if form.is_valid():
                from apps.payments.services import refund as refund_payment

                succeeded, failed = 0, []
                for payment in queryset.select_related("order"):
                    try:
                        refund_payment(
                            payment,
                            form.cleaned_data["amount"],
                            reason=form.cleaned_data["reason"],
                            actor=request.user,
                        )
                        succeeded += 1
                    except ValidationError as exc:
                        failed.append(f"{payment.order.number}: {exc.messages[0]}")
                if succeeded:
                    self.message_user(
                        request, f"تم تنفيذ {succeeded} استرجاعًا.", messages.SUCCESS
                    )
                for problem in failed:
                    self.message_user(request, problem, messages.ERROR)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RefundForm()
        return render(
            request,
            "admin/payment_refund.html",
            {"payments": queryset, "form": form, "title": "استرجاع مبلغ"},
        )


@admin.register(PaymentEvent)
class PaymentEventAdmin(AppendOnlyAdmin):
    list_display = ("created_at", "payment", "event_type", "provider_event_id")
    search_fields = ("provider_event_id", "payment__order__number")
    date_hierarchy = "created_at"


@admin.register(Refund)
class RefundAdmin(ExportMixin, admin.ModelAdmin):
    resource_classes = (RefundResource,)
    list_display = ("created_at", "payment", "amount", "state", "actor")
    list_filter = ("state",)
    search_fields = ("payment__order__number", "reason")
    date_hierarchy = "created_at"
    readonly_fields = ("payment", "amount", "state", "provider_reference", "actor", "created_at", "updated_at")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("payment__order", "actor")

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        """No add form, because there is no add form that could work.

        Every field on this model is read-only here — amount and state are
        decided by :func:`apps.payments.services.refund`, not typed in — so the
        add form rendered only ``reason`` and saving it hit a NOT NULL violation
        on ``amount``: a guaranteed 500 behind a visible "Add" button.

        Refunds are issued from the payment they belong to, through
        :meth:`PaymentAdmin.refund_payments`, which is the only path that checks
        the refundable balance and moves the payment state with it (INV-004).
        """
        return False

    def has_delete_permission(self, request, obj=None) -> bool:  # noqa: ARG002
        return False
