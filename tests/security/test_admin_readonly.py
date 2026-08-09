"""What the admin refuses, and how it permits (T-1302, T-1303, T-1304, T-1306).

The file is named for its centre of gravity — the records that carry no write
path at all — but a read-only claim is only meaningful next to the write paths
that *are* offered, so five properties are asserted together. Each requirement
is named on the class that proves it rather than here, so the traceability map
points at the assertions instead of at the whole file:

* the four ledgers expose no add, change or delete route, and stock levels move
  only through the validated adjustment action;
* the bulk actions that replace free-form editing validate **every** selected
  object and name each failure;
* the one screen that legitimately writes a lot at once — product creation with
  its five inlines — actually does so in one POST;
* money and full customer contact are withheld from the roles that do not need
  them, and the audit log is immutable even for a superuser.

Permissions are asserted against the *admin's own behaviour*, not against the
permission table alone: a missing permission that the view does not consult is
not a protection.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import NoReverseMatch, reverse

from apps.audit.models import AuditAction, AuditLog
from apps.inventory.models import StockItem, StockMovement
from apps.orders.models import Order, OrderLine, OrderStatus
from apps.payments.models import PaymentEvent

pytestmark = pytest.mark.django_db

PASSWORD = "Admin!2345"

#: The three ledgers FR-105 names that carry their own admin page. Order lines
#: have no page of their own; they are asserted through the order screen below.
LEDGER_MODELS = [AuditLog, PaymentEvent, StockMovement]


@pytest.fixture
def superuser(db):
    from apps.accounts.models import User

    return User.objects.create_superuser(email="root@zakey.test", password=PASSWORD)


@pytest.fixture
def admin_client_su(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def roles_installed(db):
    from django.core.management import call_command

    call_command("setup_roles", verbosity=0)


def staff_in_role(email: str, role: str):
    from apps.accounts.models import User

    user = User.objects.create_user(email=email, password=PASSWORD, is_staff=True)
    user.groups.add(Group.objects.get(name=role))
    return user


def request_for(user):
    request = RequestFactory().get("/admin/")
    request.user = user
    return request


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


def model_route(model, suffix: str) -> str:
    meta = model._meta
    return f"admin:{meta.app_label}_{meta.model_name}_{suffix}"


# ---------------------------------------------------------------------------
# FR-105 — the ledgers have no mutation path in the admin
# ---------------------------------------------------------------------------


class TestLedgersAreReadOnly:
    """FR-105: order lines, payment events, stock movements and audit records.

    Asserted against a **superuser**, deliberately. A ledger that is read-only
    only for the under-privileged is not read-only; it is merely inconvenient.
    """

    @pytest.mark.parametrize("model", LEDGER_MODELS, ids=lambda m: m.__name__)
    def test_the_admin_offers_no_add_change_or_delete(self, model, superuser):
        model_admin = site._registry[model]
        request = request_for(superuser)

        assert model_admin.has_add_permission(request) is False
        assert model_admin.has_change_permission(request) is False
        assert model_admin.has_delete_permission(request) is False

    @pytest.mark.parametrize("model", LEDGER_MODELS, ids=lambda m: m.__name__)
    def test_the_add_url_is_refused_over_http(self, model, admin_client_su):
        """Not merely a hidden button: the URL itself refuses."""
        response = admin_client_su.get(reverse(model_route(model, "add")))

        assert response.status_code == 403

    def test_a_posted_edit_to_a_stock_movement_is_refused(
        self, admin_client_su, variant, stock
    ):
        from apps.inventory import services as inventory_services

        inventory_services.adjust(variant, 4, "purchase")
        movement = StockMovement.objects.latest("id")
        before = movement.delta

        response = admin_client_su.post(
            reverse(model_route(StockMovement, "change"), args=[movement.pk]),
            {"delta": "999", "reason": "purchase"},
        )

        movement.refresh_from_db()
        assert response.status_code == 403
        assert movement.delta == before, "a POST rewrote an append-only ledger row"

    def test_order_lines_have_no_admin_page_of_their_own(self):
        """The only route to a line is the order screen, and it is read-only."""
        assert OrderLine not in site._registry
        with pytest.raises(NoReverseMatch):
            reverse("admin:orders_orderline_changelist")

    def test_the_order_line_inline_declares_every_field_read_only(self, superuser):
        from apps.orders.admin import OrderLineInline

        inline = OrderLineInline(Order, site)
        request = request_for(superuser)

        assert set(inline.readonly_fields) == set(inline.fields)
        assert inline.has_add_permission(request, None) is False
        assert inline.has_change_permission(request, None) is False
        assert inline.has_delete_permission(request, None) is False

    def test_the_order_screen_renders_lines_as_text_not_inputs(
        self, admin_client_su, variant
    ):
        order = make_order("ZK-RO-1")
        OrderLine.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            product_slug=variant.product.slug,
            sku=variant.sku,
            unit_price=variant.price,
            quantity=1,
            line_total=variant.price,
        )

        body = admin_client_su.get(
            reverse("admin:orders_order_change", args=[order.pk])
        ).content.decode()

        assert variant.sku in body, "precondition: the line is shown at all"
        assert 'name="lines-0-quantity"' not in body, "an order line was editable"
        assert 'name="lines-0-unit_price"' not in body

    def test_stock_levels_move_only_through_the_validated_action(self):
        """FR-105's second half: changes happen through explicit actions."""
        model_admin = site._registry[StockItem]

        assert "on_hand" in model_admin.readonly_fields
        assert "reserved" in model_admin.readonly_fields
        assert "adjust_stock" in model_admin.actions


# ---------------------------------------------------------------------------
# FR-107 — bulk actions validate every object and report per object
# ---------------------------------------------------------------------------


class TestBulkActionsReportPerObject:
    """FR-107: no silent failure, and no failure that stops the batch."""

    def _messages(self, response) -> list:
        return list(response.context["messages"])

    def test_a_mixed_selection_names_every_object_that_failed(self, admin_client_su):
        ok = make_order("ZK-BULK-OK", status=OrderStatus.PENDING)
        first_bad = make_order("ZK-BULK-BAD-1", status=OrderStatus.CANCELLED)
        second_bad = make_order("ZK-BULK-BAD-2", status=OrderStatus.DELIVERED)

        response = admin_client_su.post(
            reverse("admin:orders_order_changelist"),
            {
                "action": "action_confirm",
                "_selected_action": [str(o.pk) for o in (ok, first_bad, second_bad)],
            },
            follow=True,
        )

        ok.refresh_from_db()
        first_bad.refresh_from_db()
        second_bad.refresh_from_db()
        assert ok.status == OrderStatus.CONFIRMED
        assert first_bad.status == OrderStatus.CANCELLED
        assert second_bad.status == OrderStatus.DELIVERED

        errors = [m.message for m in self._messages(response) if m.level_tag == "error"]
        assert len(errors) == 2, f"expected one message per failed order, got {errors}"
        assert any(first_bad.number in text for text in errors)
        assert any(second_bad.number in text for text in errors)

        successes = [
            m.message for m in self._messages(response) if m.level_tag == "success"
        ]
        assert successes and "1" in successes[0]

    def test_an_early_failure_does_not_abort_the_rest_of_the_batch(
        self, admin_client_su
    ):
        """The order admin sorts by ``-placed_at``, so the refusal is processed
        first. A batch that stopped there would be a silent partial failure."""
        from datetime import timedelta

        from django.utils import timezone

        now = timezone.now()
        doomed = make_order("ZK-ORDER-BAD", status=OrderStatus.CANCELLED, placed_at=now)
        later = make_order(
            "ZK-ORDER-OK",
            status=OrderStatus.PENDING,
            placed_at=now - timedelta(hours=1),
        )

        admin_client_su.post(
            reverse("admin:orders_order_changelist"),
            {
                "action": "action_confirm",
                "_selected_action": [str(doomed.pk), str(later.pk)],
            },
            follow=True,
        )

        later.refresh_from_db()
        assert later.status == OrderStatus.CONFIRMED, (
            "one invalid object stopped the whole batch"
        )

    def test_a_wholly_invalid_selection_is_reported_rather_than_silent(
        self, admin_client_su
    ):
        cancelled = make_order("ZK-ALL-BAD", status=OrderStatus.CANCELLED)

        response = admin_client_su.post(
            reverse("admin:orders_order_changelist"),
            {"action": "action_confirm", "_selected_action": [str(cancelled.pk)]},
            follow=True,
        )

        messages = self._messages(response)
        assert [m.level_tag for m in messages] == ["error"]
        assert cancelled.number in messages[0].message


# ---------------------------------------------------------------------------
# FR-108 — one screen creates a complete product
# ---------------------------------------------------------------------------


#: related_name of each inline, which is also its formset prefix.
PRODUCT_INLINE_PREFIXES = (
    "variants",
    "images",
    "features",
    "specification_groups",
    "documents",
)


class TestProductCreationIsOneScreen:
    """FR-108: variants, images, features, specifications and documents inline."""

    def test_the_add_screen_carries_all_five_inline_formsets(
        self, admin_client_su, category
    ):
        body = admin_client_su.get(
            reverse("admin:catalog_product_add")
        ).content.decode()

        missing = [
            prefix
            for prefix in PRODUCT_INLINE_PREFIXES
            if f'name="{prefix}-TOTAL_FORMS"' not in body
        ]
        assert missing == [], f"inlines absent from the product add screen: {missing}"

    def test_one_post_creates_the_product_and_all_five_children(
        self, admin_client_su, category
    ):
        from apps.catalog.models import Product

        payload = {
            "name": "قفل زاكي نوفا",
            "slug": "zakey-nova",
            "short_description": "قفل ذكي جديد",
            "description": "وصف كامل للقفل الذكي الجديد.",
            "category": str(category.pk),
            "brand": "",
            "badge": "",
            "position": "0",
            "instalment_message": "",
            "seo_title": "",
            "seo_description": "",
            "status": "draft",
            "published_at_0": "",
            "published_at_1": "",
            "archived_at_0": "",
            "archived_at_1": "",
            # variants
            "variants-TOTAL_FORMS": "1",
            "variants-INITIAL_FORMS": "0",
            "variants-MIN_NUM_FORMS": "0",
            "variants-MAX_NUM_FORMS": "1000",
            "variants-0-sku": "ZK-NOVA-BLACK",
            "variants-0-finish_label": "أسود",
            "variants-0-swatch_hex": "#000000",
            "variants-0-price": "5990.00",
            "variants-0-compare_at_price": "",
            "variants-0-position": "0",
            # images
            "images-TOTAL_FORMS": "1",
            "images-INITIAL_FORMS": "0",
            "images-MIN_NUM_FORMS": "0",
            "images-MAX_NUM_FORMS": "1000",
            "images-0-legacy_path": "assets/images/products/nova.webp",
            "images-0-alt": "قفل زاكي نوفا",
            "images-0-position": "0",
            # features
            "features-TOTAL_FORMS": "1",
            "features-INITIAL_FORMS": "0",
            "features-MIN_NUM_FORMS": "0",
            "features-MAX_NUM_FORMS": "1000",
            "features-0-key": "fingerprint",
            "features-0-label": "بصمة سريعة",
            "features-0-description": "فتح خلال أقل من ثانية.",
            "features-0-position": "0",
            # specifications
            "specification_groups-TOTAL_FORMS": "1",
            "specification_groups-INITIAL_FORMS": "0",
            "specification_groups-MIN_NUM_FORMS": "0",
            "specification_groups-MAX_NUM_FORMS": "1000",
            "specification_groups-0-label": "الأبعاد",
            "specification_groups-0-position": "0",
            # documents
            "documents-TOTAL_FORMS": "1",
            "documents-INITIAL_FORMS": "0",
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "1000",
            "documents-0-label": "دليل التركيب",
            "documents-0-legacy_path": "assets/docs/nova.pdf",
            "documents-0-file_format": "PDF",
            "documents-0-position": "0",
            # related products
            "relations_from-TOTAL_FORMS": "0",
            "relations_from-INITIAL_FORMS": "0",
            "relations_from-MIN_NUM_FORMS": "0",
            "relations_from-MAX_NUM_FORMS": "1000",
        }

        response = admin_client_su.post(
            reverse("admin:catalog_product_add"), payload, follow=True
        )

        assert response.status_code == 200
        product = Product.objects.get(slug="zakey-nova")
        assert product.variants.count() == 1
        assert product.images.count() == 1
        assert product.features.count() == 1
        assert product.specification_groups.count() == 1
        assert product.documents.count() == 1


# ---------------------------------------------------------------------------
# FR-112 — money and full contact details are withheld
# ---------------------------------------------------------------------------


class _Viewer:
    """A stand-in staff viewer holding exactly the permissions it is given."""

    is_active = True
    is_staff = True

    def __init__(self, *permissions: str):
        self._permissions = set(permissions)

    def has_perm(self, permission: str, obj=None) -> bool:  # noqa: ARG002
        return permission in self._permissions


class TestFullContactIsRestricted:
    """FR-112, contact half: the phone is masked unless the permission is held."""

    def test_the_mask_is_gated_on_the_permission_itself(self, customer):
        from apps.accounts.models import CustomerProfile

        model_admin = site._registry[CustomerProfile]

        model_admin._request = RequestFactory().get("/admin/")
        model_admin._request.user = _Viewer()
        masked = model_admin.phone_display(customer)

        model_admin._request.user = _Viewer("accounts.view_full_contact")
        full = model_admin.phone_display(customer)

        assert masked != customer.phone
        assert masked == customer.masked_phone
        assert full == customer.phone

    def test_a_role_without_it_never_sees_the_number_on_the_changelist(
        self, client, roles_installed, customer
    ):
        client.force_login(staff_in_role("cs-contact@zakey.test", "Customer Service"))

        body = client.get(
            reverse("admin:accounts_customerprofile_changelist")
        ).content.decode()

        assert customer.full_name in body, "precondition: the row is listed"
        assert customer.phone not in body, "the full mobile number leaked to the list"
        assert customer.masked_phone in body


class TestFinancialSurfacesAreRestricted:
    """FR-112, money half: no payment surface for roles with no money mandate."""

    NO_MONEY_ROLES = ["Catalogue Manager", "Content Manager", "Inventory Manager"]

    @pytest.mark.parametrize("role", NO_MONEY_ROLES)
    def test_they_hold_no_payment_or_refund_permission(self, roles_installed, role):
        user = staff_in_role(f"money-{abs(hash(role))}@zakey.test", role)

        held = sorted(
            perm for perm in user.get_all_permissions() if perm.startswith("payments.")
        )

        assert held == [], f"{role} holds financial permissions: {held}"

    @pytest.mark.parametrize("role", NO_MONEY_ROLES)
    def test_the_payment_changelist_refuses_them_over_http(
        self, client, roles_installed, role
    ):
        client.force_login(staff_in_role(f"pay-{abs(hash(role))}@zakey.test", role))

        response = client.get(reverse("admin:payments_payment_changelist"))

        assert response.status_code in (302, 403)

    @pytest.mark.parametrize("role", NO_MONEY_ROLES)
    def test_the_payment_export_refuses_them(self, client, roles_installed, role):
        """Export is a bulk read of the money, so it obeys the same gate.

        Scoped to the payment export on purpose. The *order* export carries
        ``grand_total`` too and is open to every role that may read an order —
        which the approved matrix intends to be Finance-only for the financial
        columns. That divergence is a gap in the export, not something this
        test may pretend away.
        """
        client.force_login(staff_in_role(f"exp-{abs(hash(role))}@zakey.test", role))

        response = client.get(reverse("admin:payments_payment_export"))

        assert response.status_code in (302, 403)

    def test_finance_does_hold_them(self, client, roles_installed):
        """Guard the guard: withheld from everyone would prove nothing."""
        user = staff_in_role("finance-money@zakey.test", "Finance")
        client.force_login(user)

        assert user.has_perm("payments.view_payment")
        assert user.has_perm("payments.change_refund")
        assert client.get(reverse("admin:payments_payment_changelist")).status_code == 200


# ---------------------------------------------------------------------------
# FR-114 — the audit log is immutable, superuser included
# ---------------------------------------------------------------------------


@pytest.fixture
def audit_entry(db):
    return AuditLog.objects.create(
        action=AuditAction.CREATE,
        object_repr="سجل أصلي",
        changes={"field": "original"},
    )


class TestAuditRecordsAreImmutable:
    """FR-114: append-only, and the superuser is not an exception."""

    def test_updating_a_persisted_row_raises(self, audit_entry):
        from apps.audit.models import ImmutableRecordError

        audit_entry.object_repr = "سجل مُعدَّل"

        with pytest.raises(ImmutableRecordError):
            audit_entry.save()

        audit_entry.refresh_from_db()
        assert audit_entry.object_repr == "سجل أصلي"

    def test_deleting_a_persisted_row_raises(self, audit_entry):
        from apps.audit.models import ImmutableRecordError

        with pytest.raises(ImmutableRecordError):
            audit_entry.delete()

        assert AuditLog.objects.filter(pk=audit_entry.pk).exists()

    def test_the_admin_denies_all_three_operations_to_a_superuser(self, superuser):
        model_admin = site._registry[AuditLog]
        request = request_for(superuser)

        assert model_admin.has_add_permission(request) is False
        assert model_admin.has_change_permission(request) is False
        assert model_admin.has_delete_permission(request) is False

    def test_a_superuser_posting_an_edit_changes_nothing(
        self, admin_client_su, audit_entry
    ):
        response = admin_client_su.post(
            reverse("admin:audit_auditlog_change", args=[audit_entry.pk]),
            {"object_repr": "سجل مُخترق", "action": AuditAction.DELETE, "changes": "{}"},
        )

        audit_entry.refresh_from_db()
        assert response.status_code == 403
        assert audit_entry.object_repr == "سجل أصلي"
        assert audit_entry.action == AuditAction.CREATE

    def test_a_superuser_cannot_delete_through_the_admin(
        self, admin_client_su, audit_entry
    ):
        response = admin_client_su.post(
            reverse("admin:audit_auditlog_delete", args=[audit_entry.pk]),
            {"post": "yes"},
        )

        assert response.status_code == 403
        assert AuditLog.objects.filter(pk=audit_entry.pk).exists()

    def test_a_superuser_cannot_forge_a_new_row_through_the_admin(
        self, admin_client_su
    ):
        before = AuditLog.objects.count()

        response = admin_client_su.get(reverse("admin:audit_auditlog_add"))

        assert response.status_code == 403
        assert AuditLog.objects.count() == before

    def test_the_change_screen_offers_no_editable_field(
        self, admin_client_su, audit_entry
    ):
        body = admin_client_su.get(
            reverse("admin:audit_auditlog_change", args=[audit_entry.pk])
        ).content.decode()

        assert "سجل أصلي" in body, "precondition: the record is readable"
        assert 'name="object_repr"' not in body
        assert 'name="changes"' not in body

    def test_appending_a_new_record_still_works(self, db):
        """Append-only, not write-only: the log must still be writable forward."""
        before = AuditLog.objects.count()

        AuditLog.objects.create(action=AuditAction.LOGIN, object_repr="جديد")

        assert AuditLog.objects.count() == before + 1
        assert AuditLog.objects.latest("id").object_repr == "جديد"
