"""The admin attention queue — what a staff member must act on right now.

The dashboard in :mod:`apps.core.dashboard` answers "how is the shop doing".
This answers a different question: "what is waiting for me". The two are not the
same, and conflating them is why the counters there are the wrong source for an
alert bar — most of them are windowed to *today*, and an order that arrived
yesterday and still has nobody assigned to it is exactly the thing an alert must
not hide.

Everything here is therefore unwindowed by design: a pending payment from three
weeks ago is more urgent than one from this morning, not less.

Three constraints keep it cheap enough to run on every admin page:

* **Cached.** One set of counts serves every staff member for
  ``CACHE_TTL`` seconds. The numbers do not depend on who is looking — only on
  which of them a viewer is *allowed* to see, which is applied after the cache.
* **Counted, never fetched.** Every query is a ``COUNT`` over an indexed column.
  No rows are loaded and nothing is serialised into the session.
* **Bounded in number.** Adding a source here costs one query on every admin
  page for every process, forever. It has to earn that.

A count of zero is not an alert. Sources that are clear are dropped, so the bar
shows a short list of real work rather than a wall of reassuring noise.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.core.cache import cache

#: One minute. Long enough that a burst of admin navigation costs one round of
#: queries, short enough that a staff member who resolves something sees the
#: count fall while they are still looking at the page.
CACHE_TTL = 60

CACHE_KEY = "zakey:admin:attention:v1"

#: Severity, highest first. `critical` means money or a customer is waiting;
#: `warning` means it will become critical if ignored; `info` is a backlog.
LEVEL_ORDER = {"critical": 0, "warning": 1, "info": 2}


@dataclass(frozen=True)
class Alert:
    """One actionable count.

    ``url`` must land on a changelist *already filtered* to the same set the
    count describes. An alert that says 7 and opens a list of 4,000 is worse
    than no alert: it moves the work of finding the seven onto the reader.
    """

    key: str
    label: str
    count: int
    url: str
    level: str = "warning"
    icon: str = "fas fa-bell"
    permission: str = ""

    @property
    def level_rank(self) -> int:
        return LEVEL_ORDER.get(self.level, 99)


def _counts() -> dict[str, int]:
    """Every count in one place, so the cache holds one plain dict."""
    from apps.content.models import ContactMessage, ContactMessageStatus
    from apps.inventory.models import StockItem
    from apps.orders.models import FulfillmentStatus, Order, OrderStatus, PaymentStatus
    from apps.payments.models import Payment, PaymentState, Refund, RefundState
    from apps.reviews.models import Review, ReviewStatus

    from django.db.models import Count, F, Q

    # One grouped pass over orders rather than three round trips.
    orders = Order.objects.aggregate(
        awaiting_confirmation=Count("id", filter=Q(status=OrderStatus.PENDING)),
        paid_unfulfilled=Count(
            "id",
            filter=Q(
                payment_status=PaymentStatus.PAID,
                fulfillment_status=FulfillmentStatus.UNFULFILLED,
            )
            & ~Q(status__in=[OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
        ),
    )

    return {
        "orders_awaiting_confirmation": orders["awaiting_confirmation"] or 0,
        "orders_paid_unfulfilled": orders["paid_unfulfilled"] or 0,
        # No payment provider is integrated, so every payment on a manual method
        # sits in PENDING until a human confirms it against the bank. This is
        # the single most time-sensitive queue in the shop.
        "payments_pending": Payment.objects.filter(state=PaymentState.PENDING).count(),
        "refunds_pending": Refund.objects.filter(state=RefundState.PENDING).count(),
        "contact_new": ContactMessage.objects.filter(
            status=ContactMessageStatus.NEW
        ).count(),
        "reviews_pending": Review.objects.filter(status=ReviewStatus.PENDING).count(),
        # Sellable stock is on_hand minus what carts have reserved.
        "out_of_stock": StockItem.objects.filter(on_hand__lte=F("reserved")).count(),
        "low_stock": _low_stock_count(),
    }


def _low_stock_count() -> int:
    """Reuse the dashboard's SQL-side threshold comparison (FR-027)."""
    from apps.core.dashboard import _low_stock_count as dashboard_low_stock

    return dashboard_low_stock()


def _build(counts: dict[str, int]) -> list[Alert]:
    from apps.content.models import ContactMessageStatus
    from apps.orders.models import FulfillmentStatus, OrderStatus, PaymentStatus
    from apps.payments.models import PaymentState, RefundState
    from apps.reviews.models import ReviewStatus

    orders = "/admin/orders/order/"
    return [
        Alert(
            "payments_pending",
            "مدفوعات بانتظار التأكيد",
            counts["payments_pending"],
            f"/admin/payments/payment/?state__exact={PaymentState.PENDING}",
            level="critical",
            icon="fas fa-credit-card",
            permission="payments.view_payment",
        ),
        Alert(
            "orders_paid_unfulfilled",
            "طلبات مدفوعة بانتظار التجهيز",
            counts["orders_paid_unfulfilled"],
            f"{orders}?payment_status__exact={PaymentStatus.PAID}"
            f"&fulfillment_status__exact={FulfillmentStatus.UNFULFILLED}",
            level="critical",
            icon="fas fa-box-open",
            permission="orders.view_order",
        ),
        Alert(
            "orders_awaiting_confirmation",
            "طلبات جديدة بانتظار التأكيد",
            counts["orders_awaiting_confirmation"],
            f"{orders}?status__exact={OrderStatus.PENDING}",
            level="critical",
            icon="fas fa-receipt",
            permission="orders.view_order",
        ),
        Alert(
            "refunds_pending",
            "استرجاعات قيد التنفيذ",
            counts["refunds_pending"],
            f"/admin/payments/refund/?state__exact={RefundState.PENDING}",
            level="critical",
            icon="fas fa-undo",
            permission="payments.view_refund",
        ),
        Alert(
            "contact_new",
            "رسائل تواصل جديدة",
            counts["contact_new"],
            f"/admin/content/contactmessage/?status__exact={ContactMessageStatus.NEW}",
            level="warning",
            icon="fas fa-envelope",
            permission="content.view_contactmessage",
        ),
        Alert(
            "out_of_stock",
            "نفد من المخزون",
            counts["out_of_stock"],
            "/admin/inventory/stockitem/",
            level="warning",
            icon="fas fa-warehouse",
            permission="inventory.view_stockitem",
        ),
        Alert(
            "reviews_pending",
            "مراجعات بانتظار الموافقة",
            counts["reviews_pending"],
            f"/admin/reviews/review/?status__exact={ReviewStatus.PENDING}",
            level="warning",
            icon="fas fa-star",
            permission="reviews.view_review",
        ),
        Alert(
            "low_stock",
            "مخزون منخفض",
            counts["low_stock"],
            "/admin/inventory/stockitem/",
            level="info",
            icon="fas fa-triangle-exclamation",
            permission="inventory.view_stockitem",
        ),
    ]


def attention_alerts(user=None) -> list[Alert]:
    """Non-zero alerts this ``user`` is allowed to see, most urgent first.

    ``user=None`` skips permission filtering; that is for tests and the command
    line. The admin always passes the request's user, because these counts are
    reads of privileged data and must obey the same role matrix as the
    changelists they link to (FR-111) — a content editor has no business
    learning how many payments are outstanding.
    """
    counts = cache.get(CACHE_KEY)
    if counts is None:
        counts = _counts()
        cache.set(CACHE_KEY, counts, CACHE_TTL)

    alerts = [a for a in _build(counts) if a.count > 0]
    if user is not None:
        alerts = [a for a in alerts if not a.permission or user.has_perm(a.permission)]
    return sorted(alerts, key=lambda a: (a.level_rank, -a.count))


def invalidate() -> None:
    """Drop the cached counts.

    Called after a staff action that resolves one of the queues, so the bar does
    not keep advertising work that is already done.
    """
    cache.delete(CACHE_KEY)
