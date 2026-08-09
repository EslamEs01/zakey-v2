"""Audit signals and staff authentication logging (T-1406, T-1407, FR-113, FR-115).

The property under test is coverage of the paths a *service* never sees: a
direct admin edit, a shell session, a bulk import. Services log the interesting
domain events themselves; these receivers make sure nothing significant happens
with no record at all.

One rule is absolute and gets its own test: **a failed login must never record
the password that was tried.** An audit log that captures credentials is worse
than no audit log, because it turns the safest table into the most dangerous.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth.models import Group, Permission
from django.urls import reverse

from apps.audit.models import AuditAction, AuditLog

pytestmark = pytest.mark.django_db

PASSWORD = "StrongPass!234"


@pytest.fixture
def staff(db):
    from apps.accounts.models import User

    return User.objects.create_user(
        email="staff@zakey.test", password=PASSWORD, is_staff=True
    )


def latest(action):
    return AuditLog.objects.filter(action=action).latest("id")


# ---------------------------------------------------------------------------
# T-1407 — staff authentication logging (FR-115)
# ---------------------------------------------------------------------------


class TestAuthenticationLogging:
    def test_a_successful_login_is_logged(self, client, staff):
        client.post(
            reverse("storefront:account-login"),
            {"email": "staff@zakey.test", "password": PASSWORD},
            follow=True,
        )

        entry = latest(AuditAction.LOGIN)
        assert entry.actor_id == staff.pk
        assert entry.changes["is_staff"] is True

    def test_a_failed_login_is_logged(self, client, staff):
        client.post(
            reverse("storefront:account-login"),
            {"email": "staff@zakey.test", "password": "wrong-password"},
            follow=True,
        )

        entry = latest(AuditAction.LOGIN_FAILED)
        assert entry.changes["identifier"] == "staff@zakey.test"
        assert entry.changes["account_exists"] is True

    def test_a_failed_login_never_records_the_password(self, client, staff):
        secret = "Sup3rSecret-Never-Log-Me"

        client.post(
            reverse("storefront:account-login"),
            {"email": "staff@zakey.test", "password": secret},
            follow=True,
        )

        serialised = "".join(
            str(row) for row in AuditLog.objects.values_list("changes", flat=True)
        )
        assert secret not in serialised, "the audit log captured a submitted password"

    def test_a_failed_login_for_an_unknown_address_is_still_logged(self, client, db):
        client.post(
            reverse("storefront:account-login"),
            {"email": "ghost@example.com", "password": "whatever"},
            follow=True,
        )

        entry = latest(AuditAction.LOGIN_FAILED)
        assert entry.changes["account_exists"] is False
        assert entry.actor is None

    def test_a_logout_is_logged(self, client, staff):
        client.force_login(staff)

        client.post(reverse("storefront:account-logout"), follow=True)

        assert latest(AuditAction.LOGOUT).actor_id == staff.pk

    def test_the_admin_login_is_logged_too(self, client, staff):
        """FR-115 is about staff, so the admin's own form must be covered."""
        staff.set_password(PASSWORD)
        staff.save()

        client.post(
            reverse("admin:login"),
            {"username": "staff@zakey.test", "password": PASSWORD, "next": "/admin/"},
        )

        assert AuditLog.objects.filter(
            action=AuditAction.LOGIN, actor=staff
        ).exists()


# ---------------------------------------------------------------------------
# T-1406 — permission changes are security events
# ---------------------------------------------------------------------------


class TestPermissionChangeLogging:
    def test_adding_a_user_to_a_group_is_logged(self, staff, db):
        group = Group.objects.create(name="Temporary")

        staff.groups.add(group)

        entry = latest(AuditAction.PERMISSION_CHANGE)
        assert entry.changes["relation"] == "User_groups"
        assert entry.changes["action"] == "post_add"

    def test_removing_a_user_from_a_group_is_logged(self, staff, db):
        group = Group.objects.create(name="Temporary")
        staff.groups.add(group)

        staff.groups.remove(group)

        assert latest(AuditAction.PERMISSION_CHANGE).changes["action"] == "post_remove"

    def test_granting_a_direct_permission_is_logged(self, staff, db):
        permission = Permission.objects.filter(codename="view_order").first()

        staff.user_permissions.add(permission)

        assert latest(AuditAction.PERMISSION_CHANGE).changes["relation"] == (
            "User_user_permissions"
        )

    def test_changing_a_groups_permissions_is_logged(self, db):
        group = Group.objects.create(name="Temporary")
        permission = Permission.objects.filter(codename="view_order").first()

        group.permissions.add(permission)

        assert latest(AuditAction.PERMISSION_CHANGE).changes["relation"] == (
            "Group_permissions"
        )

    def test_granting_staff_is_logged(self, db):
        from apps.accounts.models import User

        user = User.objects.create_user(email="promoted@zakey.test", password=PASSWORD)

        user.is_staff = True
        user.save()

        entry = latest(AuditAction.PERMISSION_CHANGE)
        assert entry.changes["is_staff"] == {"before": False, "after": True}

    def test_granting_superuser_is_logged(self, staff):
        staff.is_superuser = True
        staff.save()

        assert latest(AuditAction.PERMISSION_CHANGE).changes["is_superuser"] == {
            "before": False,
            "after": True,
        }

    def test_an_unrelated_save_logs_no_permission_change(self, staff):
        before = AuditLog.objects.filter(action=AuditAction.PERMISSION_CHANGE).count()

        staff.last_login = None
        staff.save()

        after = AuditLog.objects.filter(action=AuditAction.PERMISSION_CHANGE).count()
        assert after == before, "a harmless save was logged as a permission change"


# ---------------------------------------------------------------------------
# T-1406 — price changes
# ---------------------------------------------------------------------------


class TestPriceChangeLogging:
    def test_a_price_change_is_logged(self, variant):
        variant.price = Decimal("8990.00")
        variant.save()

        entry = latest(AuditAction.PRICE_CHANGE)
        assert entry.changes["price"]["after"] == "8990.00"
        assert entry.changes["price"]["before"] == "7490.00"

    def test_saving_without_changing_the_price_logs_nothing(self, variant):
        before = AuditLog.objects.filter(action=AuditAction.PRICE_CHANGE).count()

        variant.finish_label = "أسود"
        variant.save()

        after = AuditLog.objects.filter(action=AuditAction.PRICE_CHANGE).count()
        assert after == before

    def test_creating_a_variant_is_not_a_price_change(self, product):
        from apps.catalog.models import ProductVariant

        before = AuditLog.objects.filter(action=AuditAction.PRICE_CHANGE).count()

        ProductVariant.objects.create(
            product=product, sku="ZK-NEW", finish_id="f", finish_label="جديد",
            price=Decimal("100.00"),
        )

        after = AuditLog.objects.filter(action=AuditAction.PRICE_CHANGE).count()
        assert after == before


# ---------------------------------------------------------------------------
# T-1406 — order, payment, refund, stock and coupon mutations
# ---------------------------------------------------------------------------


class TestTrackedModelLogging:
    def _order(self, number="ZK-SIG-1"):
        from apps.orders.models import Order

        return Order.objects.create(
            number=number,
            email="nada@example.com",
            phone="01012345678",
            idempotency_key=f"key-{number}",
            subtotal=Decimal("7490.00"),
            grand_total=Decimal("7490.00"),
        )

    def test_creating_an_order_is_logged(self, db):
        order = self._order()

        assert AuditLog.objects.filter(
            action=AuditAction.CREATE, object_id=str(order.pk)
        ).exists()

    def test_updating_an_order_is_logged(self, db):
        order = self._order()

        order.phone = "01099999999"
        order.save()

        assert AuditLog.objects.filter(
            action=AuditAction.UPDATE, object_id=str(order.pk)
        ).exists()

    def test_creating_a_coupon_is_logged(self, db):
        from apps.promotions.models import Coupon

        coupon = Coupon.objects.create(
            code="SIGNAL10", discount_type="percentage", value=Decimal("10.00")
        )

        assert AuditLog.objects.filter(
            action=AuditAction.CREATE, object_id=str(coupon.pk)
        ).exists()

    def test_creating_a_stock_item_is_logged(self, variant):
        from apps.inventory.models import StockItem

        item = StockItem.objects.create(variant=variant, on_hand=5)

        assert AuditLog.objects.filter(
            action=AuditAction.CREATE, object_id=str(item.pk)
        ).exists()

    def test_an_untracked_model_is_not_logged(self, category):
        """The receivers are targeted, not a blanket firehose."""
        from apps.catalog.models import Category

        before = AuditLog.objects.count()

        Category.objects.create(slug="untracked", name="غير متتبع")

        assert AuditLog.objects.count() == before


# ---------------------------------------------------------------------------
# Auditing must never break the thing being audited
# ---------------------------------------------------------------------------


def test_an_audit_failure_does_not_roll_back_the_business_write(db, monkeypatch):
    """A broken audit sink must not cost a customer their order."""
    from apps.audit import signals
    from apps.orders.models import Order

    def explode(*args, **kwargs):
        raise RuntimeError("audit sink is down")

    monkeypatch.setattr("apps.audit.services.record_audit", explode)

    order = Order.objects.create(
        number="ZK-RESILIENT",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="key-resilient",
        subtotal=Decimal("1.00"),
        grand_total=Decimal("1.00"),
    )

    assert Order.objects.filter(pk=order.pk).exists()
    assert signals is not None
