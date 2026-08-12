"""Order administration (FR-104, FR-105, FR-107).

Every financial field is read-only. Status changes go through the validated
service, never through free-form field editing, so the state machine and its
audit trail cannot be bypassed from the admin.
"""

from __future__ import annotations

from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from import_export.admin import ExportMixin

from apps.core.admin_mixins import AppendOnlyAdmin, NoDeleteAdmin, ReadOnlyInline
from apps.core.resources import OrderLineResource, OrderResource

from .models import (
    Order,
    OrderAddress,
    OrderEvent,
    OrderLine,
    OrderNote,
    OrderStatus,
)
from .services import transition

MONEY_FIELDS = (
    "subtotal",
    "discount_total",
    "coupon_code",
    "shipping_method_label",
    "shipping_total",
    "installation_requested",
    "installation_total",
    "vat_amount",
    "vat_rate",
    "grand_total",
    "used_placeholder_rates",
)


class OrderLineInline(ReadOnlyInline):
    model = OrderLine
    fields = ("product_name", "variant_label", "sku", "unit_price", "quantity", "line_total")
    readonly_fields = fields
    verbose_name = "سطر"
    verbose_name_plural = "أسطر الطلب (غير قابلة للتعديل)"


class OrderEventInline(ReadOnlyInline):
    model = OrderEvent
    fields = ("created_at", "event_type", "from_status", "to_status", "actor", "note")
    readonly_fields = fields
    verbose_name_plural = "سجل الأحداث"


class OrderAddressInline(admin.StackedInline):
    model = OrderAddress
    extra = 0
    can_delete = False
    verbose_name_plural = "عنوان التسليم (لقطة وقت الطلب)"
    readonly_fields = ("governorate_key", "area_key")


class OrderNoteInline(admin.TabularInline):
    model = OrderNote
    extra = 0
    fields = ("body", "is_customer_visible", "author", "created_at")
    readonly_fields = ("author", "created_at")


def _bulk_transition(modeladmin, request, queryset, target: str) -> None:
    """Validate every selected order and report per object (FR-107)."""
    succeeded, failed = 0, []
    for order in queryset:
        try:
            transition(order, target, actor=request.user)
            succeeded += 1
        except ValidationError as exc:
            failed.append(f"{order.number}: {exc.messages[0]}")
    if succeeded:
        modeladmin.message_user(request, f"تم تحديث {succeeded} طلبًا.", messages.SUCCESS)
    for problem in failed:
        modeladmin.message_user(request, problem, messages.ERROR)


@admin.register(Order)
class OrderAdmin(ExportMixin, NoDeleteAdmin):
    # Export only. An order is financial history; there is no legitimate reason
    # to write one from a spreadsheet (FR-104, INV-003).
    #
    # Two shapes, chosen from the export dropdown: one row per order for
    # revenue, and one row per line for "what actually sold".
    resource_classes = (OrderResource, OrderLineResource)
    list_display = (
        "number",
        "email",
        "status",
        "payment_status",
        "fulfillment_status",
        "grand_total",
        "placed_at",
    )
    list_filter = ("status", "payment_status", "fulfillment_status", "installation_requested")
    search_fields = ("number", "email", "phone", "lines__sku", "lines__product_name")
    date_hierarchy = "placed_at"
    ordering = ("-placed_at",)
    inlines = (OrderAddressInline, OrderLineInline, OrderEventInline, OrderNoteInline)

    # Everything financial and every snapshot is read-only (FR-105, INV-003).
    readonly_fields = (
        "number",
        "customer",
        "email",
        "phone",
        "idempotency_key",
        "status",
        "payment_status",
        "fulfillment_status",
        "terms_accepted_at",
        "placed_at",
        "cancelled_at",
        "created_at",
        "updated_at",
        *MONEY_FIELDS,
    )
    fieldsets = (
        ("الطلب", {"fields": ("number", "status", "payment_status", "fulfillment_status")}),
        ("العميل", {"fields": ("customer", "email", "phone")}),
        ("المبالغ (غير قابلة للتعديل)", {"fields": MONEY_FIELDS}),
        ("الشحن", {"fields": ("tracking_number",)}),
        ("التواريخ", {"fields": ("placed_at", "terms_accepted_at", "cancelled_at")}),
        ("تقني", {"classes": ("collapse",), "fields": ("idempotency_key", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("customer", "address")
            .prefetch_related("lines")
        )

    def has_add_permission(self, request) -> bool:  # noqa: ARG002
        """Orders are created by checkout, never typed into the admin."""
        return False

    @admin.action(description="تأكيد الطلبات المختارة")
    def action_confirm(self, request, queryset):
        _bulk_transition(self, request, queryset, OrderStatus.CONFIRMED)

    @admin.action(description="بدء التجهيز")
    def action_process(self, request, queryset):
        _bulk_transition(self, request, queryset, OrderStatus.PROCESSING)

    @admin.action(description="تعليم كمشحون")
    def action_ship(self, request, queryset):
        _bulk_transition(self, request, queryset, OrderStatus.SHIPPED)

    @admin.action(description="تعليم كمُسلَّم")
    def action_deliver(self, request, queryset):
        _bulk_transition(self, request, queryset, OrderStatus.DELIVERED)

    @admin.action(description="إلغاء الطلبات المختارة")
    def action_cancel(self, request, queryset):
        _bulk_transition(self, request, queryset, OrderStatus.CANCELLED)

    @admin.action(description="ربط الطلبات كزائر بحساب صاحب البريد")
    def action_associate_guest_orders(self, request, queryset):
        """Attach selected guest orders to the account holding the same email (FR-059).

        Staff-initiated on purpose. Registration alone must never hand over an
        order history, or anyone could claim a stranger's by typing their email.
        Orders that already belong to a customer, and emails with no registered
        account, are skipped rather than guessed at.
        """
        from apps.accounts.models import CustomerProfile
        from apps.orders.services import associate_guest_orders

        associated = 0
        skipped = 0
        seen: set[int] = set()
        for order in queryset:
            if order.customer_id is not None:
                skipped += 1
                continue
            profile = CustomerProfile.objects.filter(
                user__email__iexact=order.email
            ).first()
            if profile is None:
                skipped += 1
                continue
            if profile.pk in seen:
                continue
            seen.add(profile.pk)
            associated += associate_guest_orders(profile, actor=request.user)

        self.message_user(request, f"تم ربط {associated} طلبًا؛ تُرك {skipped} دون ربط.")

    actions = (
        "action_confirm",
        "action_process",
        "action_ship",
        "action_deliver",
        "action_cancel",
        "action_associate_guest_orders",
    )


@admin.register(OrderEvent)
class OrderEventAdmin(AppendOnlyAdmin):
    list_display = ("created_at", "order", "event_type", "from_status", "to_status", "actor")
    list_filter = ("event_type", "to_status")
    search_fields = ("order__number",)
    date_hierarchy = "created_at"
