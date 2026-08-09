"""The eleven bounded admin dashboard widgets (T-1308, FR-101, FR-102).

Every widget here obeys the same three rules, and the rules are the point:

* **Indexed.** Each query filters or orders on a column that carries an index,
  so none of them degrades into a sequential scan as the tables grow.
* **Date-limited.** Anything that could grow without bound is windowed to a
  recent period rather than counting all of history.
* **Count-capped.** Every list widget slices to a hard maximum, so one busy day
  cannot turn the dashboard into a thousand-row page.

A dashboard is the one page every staff member loads all day. An unbounded
widget here is not a slow page — it is a slow *database*, for everybody.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone

#: Hard cap on every list widget. Deliberately small: the dashboard is a
#: summary, and anything longer belongs in a filtered changelist.
ROW_CAP = 10

#: Rolling window for the "recent" widgets.
RECENT_DAYS = 7

#: Window for the sales total. Longer than RECENT_DAYS because a revenue figure
#: over seven days is noise; over thirty it is a trend.
SALES_DAYS = 30


@dataclass(frozen=True)
class Widget:
    """One dashboard tile.

    ``value`` is a scalar for counters, or a list of rows for list widgets.
    ``url`` deep-links into the changelist that shows the full, filterable set,
    which is what keeps the widget itself allowed to stay capped.
    """

    key: str
    label: str
    value: object
    url: str = ""
    kind: str = "count"
    #: The permission a viewer must hold to see this tile. A dashboard that
    #: shows every widget to every staff member leaks exactly what the role
    #: matrix exists to withhold — a content editor has no business reading
    #: payment failures or customer names.
    permission: str = ""


def _today_range():
    now = timezone.now()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, now


def dashboard_widgets(user=None) -> list[Widget]:
    """Build the eleven widgets (FR-101), filtered to what ``user`` may see.

    Ordered as the specification lists them so the page and the requirement can
    be read side by side.

    Passing ``user=None`` returns the unfiltered set. That is for tests and for
    the command line; the admin always passes the request's user, because a
    dashboard is a read of privileged data and must obey the same role matrix as
    the changelists it links to (FR-111).
    """
    from apps.accounts.models import CustomerProfile
    from apps.inventory.models import StockItem, StockMovement
    from apps.orders.models import Order, OrderStatus, PaymentStatus
    from apps.payments.models import Payment, PaymentState
    from apps.reviews.models import Review, ReviewStatus

    day_start, now = _today_range()
    recent_since = now - timedelta(days=RECENT_DAYS)
    sales_since = now - timedelta(days=SALES_DAYS)

    # 1-4 and 5: one grouped pass over the indexed (status, -placed_at) window
    # rather than five separate COUNT(*) round trips.
    order_counts = Order.objects.filter(placed_at__gte=day_start).aggregate(
        today=Count("id"),
        pending=Count("id", filter=Q(status=OrderStatus.PENDING)),
        paid=Count("id", filter=Q(payment_status=PaymentStatus.PAID)),
        needs_action=Count(
            "id",
            filter=Q(status__in=[OrderStatus.PENDING, OrderStatus.CONFIRMED]),
        ),
    )

    sales = Order.objects.filter(
        placed_at__gte=sales_since,
        status__in=[
            OrderStatus.CONFIRMED,
            OrderStatus.PROCESSING,
            OrderStatus.SHIPPED,
            OrderStatus.DELIVERED,
        ],
    ).aggregate(total=Sum("grand_total"))

    # Stock counters. `available` is derived, so the comparison is expressed in
    # columns the database can evaluate without loading rows.
    stock = StockItem.objects.aggregate(
        out_of_stock=Count("id", filter=Q(on_hand__lte=models_f("reserved"))),
    )

    low_stock_count = _low_stock_count()

    widgets = [
        Widget(
            "orders_today",
            "طلبات اليوم",
            order_counts["today"] or 0,
            url="/admin/orders/order/",
            permission="orders.view_order",
        ),
        Widget(
            "orders_pending",
            "طلبات قيد الانتظار",
            order_counts["pending"] or 0,
            url=f"/admin/orders/order/?status__exact={OrderStatus.PENDING}",
            permission="orders.view_order",
        ),
        Widget(
            "orders_paid",
            "طلبات مدفوعة",
            order_counts["paid"] or 0,
            url=f"/admin/orders/order/?payment_status__exact={PaymentStatus.PAID}",
            permission="orders.view_order",
        ),
        Widget(
            "orders_needing_action",
            "طلبات تحتاج إجراء",
            order_counts["needs_action"] or 0,
            url="/admin/orders/order/",
            permission="orders.view_order",
        ),
        Widget(
            "sales_total",
            f"إجمالي المبيعات ({SALES_DAYS} يومًا)",
            sales["total"] or Decimal("0.00"),
            kind="money",
            permission="orders.view_order",
        ),
        Widget(
            "low_stock",
            "مخزون منخفض",
            low_stock_count,
            url="/admin/inventory/stockitem/",
            permission="inventory.view_stockitem",
        ),
        Widget(
            "out_of_stock",
            "نفد من المخزون",
            stock["out_of_stock"] or 0,
            url="/admin/inventory/stockitem/",
            permission="inventory.view_stockitem",
        ),
        Widget(
            "reviews_pending",
            "مراجعات بانتظار الموافقة",
            Review.objects.filter(status=ReviewStatus.PENDING).count(),
            url=f"/admin/reviews/review/?status__exact={ReviewStatus.PENDING}",
            permission="reviews.view_review",
        ),
        Widget(
            "recent_customers",
            "أحدث العملاء",
            list(
                CustomerProfile.objects.filter(created_at__gte=recent_since)
                .select_related("user")
                .order_by("-created_at")[:ROW_CAP]
            ),
            url="/admin/accounts/customerprofile/",
            kind="list",
            permission="accounts.view_customerprofile",
        ),
        Widget(
            "recent_payment_failures",
            "محاولات دفع فاشلة",
            list(
                Payment.objects.filter(
                    state=PaymentState.FAILED, created_at__gte=recent_since
                )
                .select_related("order", "method")
                .order_by("-created_at")[:ROW_CAP]
            ),
            url=f"/admin/payments/payment/?state__exact={PaymentState.FAILED}",
            kind="list",
            permission="payments.view_payment",
        ),
        Widget(
            "recent_stock_movements",
            "أحدث حركات المخزون",
            list(
                StockMovement.objects.filter(created_at__gte=recent_since)
                .select_related("stock_item__variant__product")
                .order_by("-created_at", "-id")[:ROW_CAP]
            ),
            url="/admin/inventory/stockmovement/",
            kind="list",
            permission="inventory.view_stockmovement",
        ),
    ]

    if user is None:
        return widgets
    return [w for w in widgets if not w.permission or user.has_perm(w.permission)]


def models_f(name: str):
    """Local alias so the aggregate above reads as one expression."""
    from django.db.models import F

    return F(name)


def _low_stock_count() -> int:
    """Count items at or below their effective low-stock threshold (FR-027).

    The threshold is per item with a site-wide fallback, so the comparison is
    pushed into SQL with ``Coalesce`` rather than resolved in Python — the
    property version would load every stock row to count a handful.
    """
    from django.db.models import F, IntegerField, Value
    from django.db.models.functions import Coalesce

    from apps.core.models import SiteSetting
    from apps.inventory.models import StockItem

    default_threshold = SiteSetting.objects.get_solo().low_stock_threshold

    return (
        StockItem.objects.annotate(
            available_qty=F("on_hand") - F("reserved"),
            threshold=Coalesce(
                "low_stock_threshold",
                Value(default_threshold, output_field=IntegerField()),
            ),
        )
        .filter(available_qty__gt=0, available_qty__lte=F("threshold"))
        .count()
    )
