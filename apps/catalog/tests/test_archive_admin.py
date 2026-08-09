"""Archive policy as staff actually meet it, in the admin (T-0510, FR-109, FR-111).

The service layer is tested in ``test_archive_policy``. What matters here is
that the admin cannot route *around* it: not through the delete button, not
through the bulk action, not through a crafted POST.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.admin.sites import site
from django.urls import reverse

from apps.audit.models import AuditAction, AuditLog
from apps.catalog.models import Category, Collection, Product
from apps.core.models import PublicationStatus
from apps.orders.models import Order, OrderLine

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client_staff(client, db):
    from apps.accounts.models import User

    staff = User.objects.create_superuser(email="admin@zakey.test", password="Admin!2345")
    client.force_login(staff)
    return client


def order_line_for(variant, number: str = "ZK-ADM-1") -> OrderLine:
    order = Order.objects.create(
        number=number,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=f"key-{number}",
        subtotal=Decimal("7490.00"),
        grand_total=Decimal("7490.00"),
    )
    return OrderLine.objects.create(
        order=order,
        variant=variant,
        product_name=variant.product.name,
        product_slug=variant.product.slug,
        sku=variant.sku,
        unit_price=variant.price,
        quantity=1,
        line_total=variant.price,
    )


class TestAdminDeletionIsGuarded:
    def test_deleting_an_ordered_product_through_the_admin_is_refused(
        self, admin_client_staff, product, variant
    ):
        order_line_for(variant)
        url = reverse("admin:catalog_product_delete", args=[product.pk])

        response = admin_client_staff.post(url, {"post": "yes"}, follow=True)

        assert response.status_code == 200
        assert Product.objects.filter(pk=product.pk).exists(), (
            "the admin deleted a product an order depends on"
        )

    def test_the_bulk_delete_action_cannot_bypass_the_guard(
        self, admin_client_staff, product, variant
    ):
        order_line_for(variant)
        url = reverse("admin:catalog_product_changelist")

        admin_client_staff.post(
            url,
            {"action": "delete_selected", "_selected_action": [str(product.pk)], "post": "yes"},
            follow=True,
        )

        assert Product.objects.filter(pk=product.pk).exists()

    def test_an_unreferenced_product_still_deletes_and_is_audited(
        self, admin_client_staff, product, variant
    ):
        url = reverse("admin:catalog_product_delete", args=[product.pk])

        admin_client_staff.post(url, {"post": "yes"}, follow=True)

        assert not Product.objects.filter(pk=product.pk).exists()
        assert AuditLog.objects.filter(action=AuditAction.DELETE).exists()


class TestAdminArchiveActions:
    def test_archive_action_archives_and_audits(self, admin_client_staff, product):
        url = reverse("admin:catalog_product_changelist")

        admin_client_staff.post(
            url,
            {"action": "archive_selected", "_selected_action": [str(product.pk)]},
            follow=True,
        )

        product.refresh_from_db()
        assert product.status == PublicationStatus.ARCHIVED
        assert AuditLog.objects.filter(action=AuditAction.ARCHIVE).exists()

    def test_archive_action_records_the_acting_staff_member(
        self, admin_client_staff, product
    ):
        url = reverse("admin:catalog_product_changelist")

        admin_client_staff.post(
            url,
            {"action": "archive_selected", "_selected_action": [str(product.pk)]},
            follow=True,
        )

        entry = AuditLog.objects.filter(action=AuditAction.ARCHIVE).latest("id")
        assert entry.actor is not None, "an archive with no attributable actor is not evidence"
        assert entry.actor.email == "admin@zakey.test"

    def test_restore_action_returns_a_draft(self, admin_client_staff, product):
        from apps.catalog import services

        services.archive(product)
        url = reverse("admin:catalog_product_changelist")

        admin_client_staff.post(
            url,
            {"action": "restore_selected", "_selected_action": [str(product.pk)]},
            follow=True,
        )

        product.refresh_from_db()
        assert product.status == PublicationStatus.DRAFT

    def test_an_ordered_product_can_still_be_archived_from_the_admin(
        self, admin_client_staff, product, variant
    ):
        """Archiving is the offered alternative, so it must actually work."""
        order_line_for(variant)
        url = reverse("admin:catalog_product_changelist")

        admin_client_staff.post(
            url,
            {"action": "archive_selected", "_selected_action": [str(product.pk)]},
            follow=True,
        )

        product.refresh_from_db()
        assert product.status == PublicationStatus.ARCHIVED


class TestArchivedRecordsStayVisibleToStaff:
    def test_the_changelist_still_lists_an_archived_product(
        self, admin_client_staff, product
    ):
        from apps.catalog import services

        services.archive(product)
        url = reverse("admin:catalog_product_changelist")

        body = admin_client_staff.get(url).content.decode()

        assert product.name in body, "archiving must hide a record from customers, not staff"

    def test_status_is_filterable_so_archives_can_be_found(self, admin_client_staff):
        model_admin = site._registry[Product]
        assert "status" in model_admin.list_filter


class TestEveryArchivableAdminUsesThePolicy:
    @pytest.mark.parametrize("model", [Product, Category, Collection])
    def test_archive_and_restore_actions_are_registered(self, model):
        from apps.core.admin_mixins import ArchivableAdmin

        model_admin = site._registry[model]
        assert isinstance(model_admin, ArchivableAdmin), (
            f"{model.__name__} admin bypasses the archive policy"
        )
        assert "archive_selected" in model_admin.actions
        assert "restore_selected" in model_admin.actions
