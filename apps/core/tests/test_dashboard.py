"""Admin dashboard and changelist query budgets (T-1308, T-1310, FR-101, FR-102, FR-106).

Two separate promises are tested here.

The dashboard must show the eleven things the specification names — and must
stay **bounded** while doing it. A dashboard is the page every staff member
loads all day, so an unbounded widget is not a slow page, it is a slow database
for everybody.

The changelists must stay within a documented query budget. The budgets are
asserted as *ceilings*, so adding a column that triggers an N+1 fails the build
instead of quietly costing a query per row.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse

from apps.core.dashboard import ROW_CAP, dashboard_widgets
from apps.orders.models import Order

pytestmark = pytest.mark.django_db

#: Ceiling for one full dashboard build (FR-102). It currently costs 9; the
#: headroom absorbs a widget or two without hiding an N+1, which would show up
#: as a count that scales with the fixtures rather than as a fixed overrun.
DASHBOARD_QUERY_BUDGET = 15

#: The eleven widgets FR-101 names, in specification order.
REQUIRED_WIDGETS = [
    "orders_today",
    "orders_pending",
    "orders_paid",
    "orders_needing_action",
    "sales_total",
    "low_stock",
    "out_of_stock",
    "reviews_pending",
    "recent_customers",
    "recent_payment_failures",
    "recent_stock_movements",
]


@pytest.fixture
def staff_client(client, db):
    from apps.accounts.models import User

    staff = User.objects.create_superuser(email="admin@zakey.test", password="Admin!2345")
    client.force_login(staff)
    return client


def make_order(number: str, **kwargs) -> Order:
    from django.utils import timezone

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


# ---------------------------------------------------------------------------
# FR-101: all eleven widgets, and the right ones
# ---------------------------------------------------------------------------


class TestWidgetCoverage:
    def test_all_eleven_widgets_are_present(self, site_setting):
        keys = [w.key for w in dashboard_widgets()]
        assert keys == REQUIRED_WIDGETS

    def test_there_are_exactly_eleven(self, site_setting):
        assert len(dashboard_widgets()) == 11

    def test_every_widget_is_labelled_in_arabic(self, site_setting):
        for widget in dashboard_widgets():
            assert widget.label.strip(), f"{widget.key} has no label"
            assert any("؀" <= ch <= "ۿ" for ch in widget.label), (
                f"{widget.key} is not labelled in Arabic"
            )


# ---------------------------------------------------------------------------
# The counters count the right things
# ---------------------------------------------------------------------------


class TestWidgetValues:
    def _by_key(self, site_setting):
        return {w.key: w.value for w in dashboard_widgets()}

    def test_orders_today_counts_only_today(self, site_setting):
        from datetime import timedelta

        from django.utils import timezone

        make_order("ZK-TODAY")
        old = make_order("ZK-OLD")
        Order.objects.filter(pk=old.pk).update(
            placed_at=timezone.now() - timedelta(days=3)
        )

        assert self._by_key(site_setting)["orders_today"] == 1

    def test_pending_orders_are_counted(self, site_setting):
        from apps.orders.models import OrderStatus

        make_order("ZK-P1", status=OrderStatus.PENDING)
        make_order("ZK-P2", status=OrderStatus.CANCELLED)

        assert self._by_key(site_setting)["orders_pending"] == 1

    def test_paid_orders_are_counted(self, site_setting):
        from apps.orders.models import PaymentStatus

        make_order("ZK-PAID", payment_status=PaymentStatus.PAID)
        make_order("ZK-UNPAID")

        assert self._by_key(site_setting)["orders_paid"] == 1

    def test_sales_total_excludes_cancelled_orders(self, site_setting):
        from apps.orders.models import OrderStatus

        make_order("ZK-S1", status=OrderStatus.DELIVERED)
        make_order("ZK-S2", status=OrderStatus.CANCELLED)

        assert self._by_key(site_setting)["sales_total"] == Decimal("7490.00")

    def test_low_stock_uses_the_effective_threshold(self, site_setting, variant, stock):
        from apps.inventory.models import StockItem

        StockItem.objects.filter(pk=stock.pk).update(on_hand=2, low_stock_threshold=5)

        assert self._by_key(site_setting)["low_stock"] == 1

    def test_out_of_stock_counts_zero_availability(self, site_setting, variant, stock):
        from apps.inventory.models import StockItem

        StockItem.objects.filter(pk=stock.pk).update(on_hand=0)

        assert self._by_key(site_setting)["out_of_stock"] == 1

    def test_a_fully_reserved_item_counts_as_out_of_stock(
        self, site_setting, variant, stock
    ):
        """Availability is on_hand minus reserved, not on_hand alone."""
        from apps.inventory.models import StockItem

        StockItem.objects.filter(pk=stock.pk).update(on_hand=5, reserved=5)

        assert self._by_key(site_setting)["out_of_stock"] == 1

    def test_pending_reviews_are_counted(self, site_setting, product, customer):
        from apps.reviews.models import Review, ReviewStatus

        Review.objects.create(
            product=product, customer=customer, rating=5, body="ممتاز",
            status=ReviewStatus.PENDING,
        )

        assert self._by_key(site_setting)["reviews_pending"] == 1


# ---------------------------------------------------------------------------
# FR-102: bounded. This is the load-bearing part.
# ---------------------------------------------------------------------------


class TestWidgetsAreBounded:
    def test_every_list_widget_is_capped(self, site_setting, customer):
        from apps.accounts.models import CustomerProfile, User

        for index in range(ROW_CAP + 5):
            user = User.objects.create_user(
                email=f"bulk{index}@example.com", password="StrongPass!234"
            )
            CustomerProfile.objects.create(
                user=user, full_name=f"عميل {index}", phone="01012345678"
            )

        recent = next(w for w in dashboard_widgets() if w.key == "recent_customers")
        assert len(recent.value) == ROW_CAP, "a list widget grew with the table"

    def test_the_dashboard_query_budget_holds(
        self, django_assert_max_num_queries, site_setting
    ):
        """T-1308's named acceptance test.

        A ceiling, not an equality: the point is that the number does not grow
        with the size of the tables. It currently sits at 9.
        """
        with django_assert_max_num_queries(DASHBOARD_QUERY_BUDGET):
            dashboard_widgets()

    def test_the_budget_does_not_grow_with_the_data(
        self, django_assert_max_num_queries, site_setting, variant, stock, customer
    ):
        """The N+1 detector. Same query count against a much larger dataset."""
        from apps.accounts.models import CustomerProfile, User
        from apps.inventory import services as inventory_services

        for index in range(12):
            make_order(f"ZK-BULK-{index}")
            user = User.objects.create_user(
                email=f"many{index}@example.com", password="StrongPass!234"
            )
            CustomerProfile.objects.create(
                user=user, full_name=f"عميل {index}", phone="01012345678"
            )
        inventory_services.adjust(variant, 3, "purchase")

        with django_assert_max_num_queries(DASHBOARD_QUERY_BUDGET):
            dashboard_widgets()

    def test_widgets_render_on_the_admin_index(self, staff_client, site_setting):
        response = staff_client.get(reverse("admin:index"))

        assert response.status_code == 200
        assert "zakey_widgets" in response.context
        assert len(response.context["zakey_widgets"]) == 11

    def test_the_dashboard_is_not_computed_on_other_admin_pages(
        self, staff_client, site_setting
    ):
        """Eleven aggregates belong on the dashboard, not on every changelist."""
        response = staff_client.get(reverse("admin:orders_order_changelist"))

        assert response.status_code == 200
        assert "zakey_widgets" not in response.context


# ---------------------------------------------------------------------------
# FR-111: the dashboard obeys the role matrix
# ---------------------------------------------------------------------------


class TestDashboardRespectsPermissions:
    """A dashboard is a read of privileged data.

    Showing every tile to every staff member would leak exactly what the role
    matrix exists to withhold — and it would do it on the first page everyone
    sees, which is the worst possible place for it.
    """

    @pytest.fixture
    def roled_client(self, client, db):
        from django.core.management import call_command

        call_command("setup_roles", verbosity=0)

        def _login(role: str):
            from django.contrib.auth.models import Group

            from apps.accounts.models import User

            user = User.objects.create_user(
                email=f"{role.replace(' ', '-').lower()}@zakey.test",
                password="StrongPass!234",
                is_staff=True,
            )
            user.groups.add(Group.objects.get(name=role))
            client.force_login(user)
            return client

        return _login

    def test_a_content_manager_sees_no_payment_widget(self, roled_client, site_setting):
        client = roled_client("Content Manager")

        response = client.get(reverse("admin:index"))

        keys = {w.key for w in response.context["zakey_widgets"]}
        assert "recent_payment_failures" not in keys
        assert "orders_today" not in keys

    def test_a_content_manager_sees_no_payment_link_on_the_page(
        self, roled_client, site_setting
    ):
        client = roled_client("Content Manager")

        body = client.get(reverse("admin:index")).content.decode()

        assert "/admin/payments/payment/" not in body

    def test_finance_does_see_the_payment_widget(self, roled_client, site_setting):
        client = roled_client("Finance")

        response = client.get(reverse("admin:index"))

        keys = {w.key for w in response.context["zakey_widgets"]}
        assert "recent_payment_failures" in keys

    def test_a_superuser_sees_all_eleven(self, staff_client, site_setting):
        response = staff_client.get(reverse("admin:index"))

        assert len(response.context["zakey_widgets"]) == 11

    def test_a_staff_user_with_no_role_sees_nothing(self, client, db, site_setting):
        from apps.accounts.models import User

        user = User.objects.create_user(
            email="norole@zakey.test", password="StrongPass!234", is_staff=True
        )
        client.force_login(user)

        response = client.get(reverse("admin:index"))

        assert response.context["zakey_widgets"] == []

    def test_every_widget_declares_a_permission(self, site_setting):
        """A tile with no permission is a tile everyone sees."""
        undeclared = [w.key for w in dashboard_widgets() if not w.permission]
        assert undeclared == [], f"widgets with no permission gate: {undeclared}"


# ---------------------------------------------------------------------------
# T-1310 / FR-106: a documented query budget on every changelist
# ---------------------------------------------------------------------------


#: Ceilings, deliberately generous enough to absorb Django's own session,
#: permission and pagination queries, but far below anything per-row.
CHANGELIST_BUDGET = 25

CHANGELIST_BUDGETS = {
    name: CHANGELIST_BUDGET
    for name in (
        "accounts_address",
        "accounts_customerprofile",
        "accounts_user",
        "audit_auditlog",
        "auth_group",
        "cart_cart",
        "cart_wishlist",
        "cart_wishlistitem",
        "catalog_brand",
        "catalog_category",
        "catalog_collection",
        "catalog_product",
        "catalog_productvariant",
        "catalog_specificationitem",
        "content_banner",
        "content_contactmessage",
        "content_faq",
        "content_homesection",
        "content_navigationitem",
        "content_newslettersubscription",
        "content_partner",
        "content_staticpage",
        "core_sitesetting",
        "inventory_stockitem",
        "inventory_stockmovement",
        "inventory_stockreservation",
        "orders_order",
        "orders_orderevent",
        "payments_payment",
        "payments_paymentevent",
        "payments_paymentmethod",
        "payments_refund",
        "promotions_coupon",
        "promotions_couponredemption",
        "reviews_review",
        "shipping_governorate",
        "shipping_installationservice",
        "shipping_servicearea",
        "shipping_shippingmethod",
        "shipping_shippingrate",
        "shipping_shippingzone",
    )
}


class TestChangelistQueryBudgets:
    @pytest.mark.parametrize("route,budget", sorted(CHANGELIST_BUDGETS.items()))
    def test_changelist_stays_within_budget(
        self, staff_client, django_assert_max_num_queries, route, budget, seeded_catalogue
    ):
        url = reverse(f"admin:{route}_changelist")

        with django_assert_max_num_queries(budget):
            response = staff_client.get(url)

        assert response.status_code == 200

    def test_every_registered_model_has_a_documented_budget(self):
        """A new model admin must not silently escape the budget regime."""
        registered = {
            f"{model._meta.app_label}_{model._meta.model_name}"
            for model in site._registry
        }
        undocumented = sorted(registered - set(CHANGELIST_BUDGETS))
        assert undocumented == [], (
            f"these changelists have no documented query budget: {undocumented}"
        )
