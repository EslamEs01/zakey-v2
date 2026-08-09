"""Guest-order association (T-1010, FR-059, ASM-002).

Guest checkout proves control of a basket. It does **not** prove control of an
inbox. So association is a staff decision, not a side effect of registering —
otherwise anyone could type a stranger's email into the signup form and inherit
their entire order history, including addresses and phone numbers.

These tests defend that boundary from both directions: the association must
work when staff ask for it, and must never happen when they do not.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import CustomerProfile, User
from apps.audit.models import AuditLog
from apps.orders.models import Order, OrderEvent
from apps.orders.services import associate_guest_orders, claimable_guest_orders

pytestmark = pytest.mark.django_db


def guest_order(email: str, number: str = "ZK-GUEST-1") -> Order:
    return Order.objects.create(
        number=number,
        email=email,
        phone="01012345678",
        idempotency_key=f"key-{number}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )


@pytest.fixture
def registered(db):
    user = User.objects.create_user(email="nada@example.com", password="StrongPass!234")
    return CustomerProfile.objects.create(
        user=user, full_name="ندى إبراهيم", phone="01012345678"
    )


# ---------------------------------------------------------------------------
# The association itself
# ---------------------------------------------------------------------------


class TestAssociation:
    def test_a_matching_guest_order_is_associated(self, registered):
        order = guest_order("nada@example.com")

        count = associate_guest_orders(registered)

        order.refresh_from_db()
        assert count == 1
        assert order.customer_id == registered.pk

    def test_email_matching_is_case_insensitive(self, registered):
        order = guest_order("Nada@Example.COM")

        associate_guest_orders(registered)

        order.refresh_from_db()
        assert order.customer_id == registered.pk

    def test_every_matching_order_is_associated(self, registered):
        first = guest_order("nada@example.com", "ZK-GUEST-1")
        second = guest_order("nada@example.com", "ZK-GUEST-2")

        count = associate_guest_orders(registered)

        first.refresh_from_db()
        second.refresh_from_db()
        assert count == 2
        assert first.customer_id == second.customer_id == registered.pk

    def test_running_twice_associates_nothing_new(self, registered):
        guest_order("nada@example.com")

        first = associate_guest_orders(registered)
        second = associate_guest_orders(registered)

        assert (first, second) == (1, 0)

    def test_no_matching_orders_is_a_safe_no_op(self, registered):
        assert associate_guest_orders(registered) == 0


# ---------------------------------------------------------------------------
# What must never be claimed
# ---------------------------------------------------------------------------


class TestBoundaries:
    def test_another_persons_order_is_never_claimed(self, registered):
        someone_else = guest_order("omar@example.com", "ZK-GUEST-9")

        associate_guest_orders(registered)

        someone_else.refresh_from_db()
        assert someone_else.customer_id is None

    def test_an_order_already_owned_is_never_moved(self, registered):
        other_user = User.objects.create_user(
            email="omar@example.com", password="StrongPass!234"
        )
        other = CustomerProfile.objects.create(
            user=other_user, full_name="عمر حسن", phone="01112345678"
        )
        order = guest_order("nada@example.com")
        order.customer = other
        order.save(update_fields=["customer"])

        associate_guest_orders(registered)

        order.refresh_from_db()
        assert order.customer_id == other.pk, "an owned order was reassigned"

    def test_claimable_never_includes_owned_orders(self, registered):
        order = guest_order("nada@example.com")
        order.customer = registered
        order.save(update_fields=["customer"])

        assert order not in claimable_guest_orders(registered)

    def test_registering_alone_does_not_associate_anything(self, client, db):
        """The account-takeover case. Registration must not hand over history."""
        order = guest_order("nada@example.com")

        client.post(
            reverse("storefront:account-register"),
            {
                "full_name": "منتحل",
                "email": "nada@example.com",
                "phone": "01012345678",
                "password": "StrongPass!234",
                "password_confirm": "StrongPass!234",
            },
            follow=True,
        )

        order.refresh_from_db()
        assert order.customer_id is None, (
            "registering with an email silently claimed a stranger's guest order"
        )

    def test_a_customer_cannot_see_an_unassociated_order(self, client, registered):
        """Until staff associate it, the order is not in the customer's history."""
        guest_order("nada@example.com")
        client.force_login(registered.user)

        response = client.get(reverse("storefront:account"))

        assert list(response.context["orders"]) == []


# ---------------------------------------------------------------------------
# Audit evidence (FR-059)
# ---------------------------------------------------------------------------


class TestAuditEvidence:
    def test_association_writes_an_audit_row(self, registered):
        guest_order("nada@example.com")

        associate_guest_orders(registered)

        entry = AuditLog.objects.filter(
            changes__reason="guest_order_association"
        ).latest("id")
        assert entry.changes["customer"]["after"] == registered.pk

    def test_the_acting_staff_member_is_recorded(self, registered, db):
        staff = User.objects.create_superuser(
            email="admin@zakey.test", password="Admin!2345"
        )
        guest_order("nada@example.com")

        associate_guest_orders(registered, actor=staff)

        entry = AuditLog.objects.filter(
            changes__reason="guest_order_association"
        ).latest("id")
        assert entry.actor_id == staff.pk, "an association with no named actor is not evidence"

    def test_the_order_gains_a_history_event(self, registered):
        order = guest_order("nada@example.com")

        associate_guest_orders(registered)

        assert OrderEvent.objects.filter(
            order=order, event_type="guest_order_association"
        ).exists()


# ---------------------------------------------------------------------------
# The staff-facing admin action
# ---------------------------------------------------------------------------


class TestAdminAction:
    @pytest.fixture
    def staff_client(self, client, db):
        staff = User.objects.create_superuser(
            email="admin@zakey.test", password="Admin!2345"
        )
        client.force_login(staff)
        return client

    def test_the_action_associates_the_selected_order(self, staff_client, registered):
        order = guest_order("nada@example.com")

        staff_client.post(
            reverse("admin:orders_order_changelist"),
            {
                "action": "action_associate_guest_orders",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )

        order.refresh_from_db()
        assert order.customer_id == registered.pk

    def test_the_action_skips_an_email_with_no_account(self, staff_client, db):
        order = guest_order("ghost@example.com")

        staff_client.post(
            reverse("admin:orders_order_changelist"),
            {
                "action": "action_associate_guest_orders",
                "_selected_action": [str(order.pk)],
            },
            follow=True,
        )

        order.refresh_from_db()
        assert order.customer_id is None

    def test_the_action_is_registered(self):
        from django.contrib.admin.sites import site

        assert "action_associate_guest_orders" in site._registry[Order].actions


# ---------------------------------------------------------------------------
# Guest checkout itself stays open (ASM-002)
# ---------------------------------------------------------------------------


def test_guest_checkout_needs_no_account(storefront):
    from apps.catalog.models import Product

    variant = Product.objects.get(slug="zakey-apex-pro").variants.first()
    storefront.post(
        reverse("storefront:cart-add"), {"variant": variant.pk, "quantity": 1}, follow=True
    )

    response = storefront.get(reverse("storefront:checkout"))

    assert response.status_code == 200
    assert response.context["cart_lines"]
