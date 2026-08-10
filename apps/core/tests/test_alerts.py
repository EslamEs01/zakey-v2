"""The admin attention queue (apps.core.alerts).

Three promises are tested here, because each of them is a way the bar could be
actively worse than having no bar at all:

* **It counts the whole backlog, not today's.** The dashboard counters are
  windowed to today on purpose; an alert must not be, or a payment that has been
  waiting a fortnight silently drops off the bar.
* **Every link lands on the set it counted.** An alert that says 7 and opens an
  unfiltered list of everything moves the work of finding the seven onto the
  reader.
* **It obeys the role matrix (FR-111).** These counts are reads of privileged
  data. A content editor learning how many payments are outstanding is the exact
  leak the permission matrix exists to prevent.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.utils import timezone

from apps.core.alerts import attention_alerts, invalidate

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _clear_alert_cache():
    """The counts are cached for a minute; tests must never see a stale set."""
    invalidate()
    yield
    invalidate()


def make_order(number: str, **kwargs):
    from apps.orders.models import Order

    defaults = {
        "email": "nada@example.com",
        "phone": "01012345678",
        "idempotency_key": f"key-{number}",
        "subtotal": Decimal("7490.00"),
        "grand_total": Decimal("7490.00"),
        "placed_at": timezone.now(),
    }
    defaults.update(kwargs)
    return Order.objects.create(number=number, **defaults)


class TestQueueContents:
    def test_a_clear_shop_raises_nothing(self, site_setting):
        assert attention_alerts(None) == []

    def test_a_pending_order_is_raised_as_critical(self, site_setting):
        from apps.orders.models import OrderStatus

        make_order("ZK-A1", status=OrderStatus.PENDING)

        alerts = {a.key: a for a in attention_alerts(None)}
        assert alerts["orders_awaiting_confirmation"].count == 1
        assert alerts["orders_awaiting_confirmation"].level == "critical"

    def test_a_paid_but_unfulfilled_order_is_raised(self, site_setting):
        from apps.orders.models import FulfillmentStatus, OrderStatus, PaymentStatus

        make_order(
            "ZK-A2",
            status=OrderStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            fulfillment_status=FulfillmentStatus.UNFULFILLED,
        )

        alerts = {a.key: a for a in attention_alerts(None)}
        assert alerts["orders_paid_unfulfilled"].count == 1

    def test_a_cancelled_order_is_not_work(self, site_setting):
        """Cancelled and refunded orders are settled, however they were paid."""
        from apps.orders.models import FulfillmentStatus, OrderStatus, PaymentStatus

        make_order(
            "ZK-A3",
            status=OrderStatus.CANCELLED,
            payment_status=PaymentStatus.PAID,
            fulfillment_status=FulfillmentStatus.UNFULFILLED,
        )

        assert {a.key for a in attention_alerts(None)} == set()

    def test_an_old_order_still_counts(self, site_setting):
        """The whole point: the backlog is not windowed to today (unlike the
        dashboard counters, which deliberately are)."""
        from datetime import timedelta

        from apps.orders.models import OrderStatus

        make_order(
            "ZK-A4",
            status=OrderStatus.PENDING,
            placed_at=timezone.now() - timedelta(days=45),
        )

        alerts = {a.key: a for a in attention_alerts(None)}
        assert alerts["orders_awaiting_confirmation"].count == 1

    def test_new_contact_messages_are_raised(self, site_setting):
        from apps.content.models import ContactMessage, ContactMessageStatus

        ContactMessage.objects.create(
            name="ندى",
            email="nada@example.com",
            subject="استفسار",
            message="رسالة اختبار طويلة بما يكفي لتجاوز الحد الأدنى المطلوب.",
            status=ContactMessageStatus.NEW,
        )

        alerts = {a.key: a for a in attention_alerts(None)}
        assert alerts["contact_new"].count == 1

    def test_zero_counts_are_dropped(self, site_setting):
        """A calm shop shows an empty bar, not eight reassuring zeroes."""
        from apps.orders.models import OrderStatus

        make_order("ZK-A5", status=OrderStatus.PENDING)

        assert all(a.count > 0 for a in attention_alerts(None))


class TestOrdering:
    def test_critical_sorts_above_warning(self, site_setting):
        from apps.content.models import ContactMessage, ContactMessageStatus
        from apps.orders.models import OrderStatus

        for i in range(5):
            ContactMessage.objects.create(
                name=f"عميل {i}",
                email=f"c{i}@example.com",
                subject="استفسار",
                message="رسالة اختبار طويلة بما يكفي لتجاوز الحد الأدنى المطلوب.",
                status=ContactMessageStatus.NEW,
            )
        make_order("ZK-B1", status=OrderStatus.PENDING)

        levels = [a.level for a in attention_alerts(None)]
        # The single critical order outranks five warnings; severity beats volume.
        assert levels[0] == "critical"


class TestLinksAreFiltered:
    def test_every_alert_links_to_a_filtered_changelist(self, site_setting, client):
        """A link must carry the same filter as the count, or open a list whose
        every row is the work (stock items have no status to filter on)."""
        from apps.orders.models import OrderStatus

        make_order("ZK-C1", status=OrderStatus.PENDING)

        for alert in attention_alerts(None):
            if alert.key in {"out_of_stock", "low_stock"}:
                continue
            assert "?" in alert.url and "__exact=" in alert.url, (
                f"{alert.key} links to an unfiltered changelist: {alert.url}"
            )

    def test_alert_links_resolve_for_a_superuser(self, site_setting, client):
        from apps.accounts.models import User
        from apps.orders.models import OrderStatus

        make_order("ZK-C2", status=OrderStatus.PENDING)
        staff = User.objects.create_superuser(email="a@zakey.test", password="Admin!2345")
        client.force_login(staff)

        for alert in attention_alerts(None):
            assert client.get(alert.url).status_code == 200, alert.url


class TestPermissions:
    def test_a_staff_member_without_permissions_sees_nothing(self, site_setting):
        from apps.accounts.models import User
        from apps.orders.models import OrderStatus

        make_order("ZK-D1", status=OrderStatus.PENDING)
        editor = User.objects.create_user(email="editor@zakey.test", password="Editor!2345")
        editor.is_staff = True
        editor.save()

        assert attention_alerts(editor) == []

    def test_a_superuser_sees_the_queue(self, site_setting):
        from apps.accounts.models import User
        from apps.orders.models import OrderStatus

        make_order("ZK-D2", status=OrderStatus.PENDING)
        staff = User.objects.create_superuser(email="b@zakey.test", password="Admin!2345")

        assert {a.key for a in attention_alerts(staff)} == {"orders_awaiting_confirmation"}


class TestRendering:
    """The bar is server-rendered EMPTY and filled from the JSON endpoint.

    Building the counts during page render cost eight COUNTs and pushed the
    catalogue and stock changelists past their 25-query budget (T-1310). The
    split is the fix, so the tests assert the split rather than the markup.
    """

    def test_the_container_ships_on_every_admin_page(self, site_setting, client):
        from apps.accounts.models import User
        from apps.orders.models import OrderStatus

        make_order("ZK-E1", status=OrderStatus.PENDING)
        staff = User.objects.create_superuser(email="c@zakey.test", password="Admin!2345")
        client.force_login(staff)

        for path in ("/admin/", "/admin/orders/order/", "/admin/catalog/product/"):
            body = client.get(path).content.decode()
            assert 'id="zk-alertbar"' in body, f"no attention bar on {path}"
            assert "zakey_admin_alerts" in body, f"bar never gets filled on {path}"

    def test_rendering_an_admin_page_costs_no_alert_queries(self, site_setting, client):
        """The whole reason the counts moved out of the page render."""
        from apps.accounts.models import User
        from apps.orders.models import OrderStatus

        make_order("ZK-E2", status=OrderStatus.PENDING)
        staff = User.objects.create_superuser(email="e@zakey.test", password="Admin!2345")
        client.force_login(staff)
        invalidate()  # cold cache: a page render must still not build the counts

        body = client.get("/admin/catalog/product/").content.decode()
        # The container is present but carries no counts, so nothing was queried
        # to produce it.
        assert 'id="zk-alertbar"' in body
        assert "zk-chip" not in body

    def test_the_endpoint_returns_the_queue(self, site_setting, client):
        from apps.accounts.models import User
        from apps.orders.models import OrderStatus

        make_order("ZK-E3", status=OrderStatus.PENDING)
        staff = User.objects.create_superuser(email="f@zakey.test", password="Admin!2345")
        client.force_login(staff)

        payload = client.get("/admin/zakey-alerts/").json()
        keys = {a["key"] for a in payload["alerts"]}
        assert keys == {"orders_awaiting_confirmation"}
        assert payload["alerts"][0]["count"] == 1

    def test_the_endpoint_is_empty_when_there_is_no_work(self, site_setting, client):
        from apps.accounts.models import User

        staff = User.objects.create_superuser(email="g@zakey.test", password="Admin!2345")
        client.force_login(staff)

        assert client.get("/admin/zakey-alerts/").json()["alerts"] == []

    def test_the_endpoint_refuses_anonymous_callers(self, site_setting, client):
        """Order volume and outstanding money are not public facts."""
        response = client.get("/admin/zakey-alerts/")
        assert response.status_code == 302
        assert "/admin/login/" in response["Location"]

    def test_the_endpoint_is_never_shared_cached(self, site_setting, client):
        from apps.accounts.models import User

        staff = User.objects.create_superuser(email="h@zakey.test", password="Admin!2345")
        client.force_login(staff)

        response = client.get("/admin/zakey-alerts/")
        assert "no-store" in response["Cache-Control"]


class TestCost:
    def test_the_queue_is_cached_between_calls(self, site_setting, django_assert_num_queries):
        from apps.orders.models import OrderStatus

        make_order("ZK-F1", status=OrderStatus.PENDING)
        attention_alerts(None)  # warms the cache

        # The second call must not re-run the counts; the bar renders on every
        # admin page and the per-page cost has to be a cache read.
        with django_assert_num_queries(0):
            attention_alerts(None)

    def test_one_cold_build_stays_within_budget(self, site_setting, django_assert_max_num_queries):
        # One COUNT per source plus the site-setting read for the stock
        # threshold. The ceiling catches a source added without thought.
        with django_assert_max_num_queries(10):
            attention_alerts(None)
