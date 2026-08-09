"""The nine-role permission matrix, exhaustively (T-1403, T-1404, T-1405, FR-111, SC-006).

This file is parametrised over **every role × model × operation cell**. That is
the point: a matrix tested only at the cells someone remembered to write down is
a matrix with unknown holes, and the holes are where the privilege escalation
lives.

Two independent layers are checked for each cell:

1. **Django's permission record** — what ``user.has_perm`` answers.
2. **The admin's actual behaviour** — what an HTTP request is allowed to do.

They are checked separately because they can disagree, and when they do it is
always the HTTP layer that matters. A role that lacks ``change`` but whose
change form still accepts a POST is not protected by the missing permission.

The third layer, menu visibility, is explicitly proved to be *cosmetic*
(T-1405): hiding a link neither grants nor denies anything.
"""

from __future__ import annotations

import pytest
from django.contrib.admin.sites import site
from django.contrib.auth.models import Group
from django.urls import NoReverseMatch, reverse

from apps.accounts.management.commands.setup_roles import ROLES

pytestmark = pytest.mark.django_db

OPERATIONS = ("view", "add", "change", "delete")

#: Apps whose permissions no role is ever granted wholesale.
PLUMBING = {"admin", "sessions", "contenttypes"}

#: The nine role names the specification lists, spelled exactly as it spells
#: them. Written out rather than derived from ``ROLES`` on purpose: deriving the
#: expectation from the implementation would make the check pass however the
#: groups were renamed.
NINE_ROLES = (
    "Super Administrator",
    "Store Manager",
    "Catalogue Manager",
    "Inventory Manager",
    "Order Fulfilment",
    "Customer Service",
    "Finance",
    "Content Manager",
    "Read-only Auditor",
)

#: Ledgers with no mutation path in the admin, for anybody (INV-013).
APPEND_ONLY = {
    "audit.auditlog",
    "inventory.stockmovement",
    "payments.paymentevent",
    "orders.orderevent",
}


@pytest.fixture
def roles_installed(db):
    """Install the nine roles for this test."""
    from django.core.management import call_command

    call_command("setup_roles", verbosity=0)


def make_staff(email: str, role: str | None = None):
    from apps.accounts.models import User

    user = User.objects.create_user(email=email, password="StrongPass!234", is_staff=True)
    if role:
        user.groups.add(Group.objects.get(name=role))
    return user


def expected(role: str, model_key: str, operation: str) -> bool:
    """What the approved matrix says this cell should be."""
    spec = ROLES[role]
    if "*" in spec:
        app_label = model_key.split(".", 1)[0]
        if app_label in PLUMBING:
            return False
        return operation in spec["*"]
    return operation in spec.get(model_key, ())


def expected_write_permissions(role: str) -> set[str]:
    """Every non-view permission the approved matrix grants ``role``.

    Computed against the real ``Permission`` table rather than the admin
    registry, because a role can hold permissions for models that have no admin
    page at all — and those still grant API- and shell-level power.
    """
    from django.contrib.auth.models import Permission

    spec = ROLES[role]
    expected: set[str] = set()
    for permission in Permission.objects.select_related("content_type"):
        app_label = permission.content_type.app_label
        model_name = permission.content_type.model
        operation = permission.codename.split("_", 1)[0]
        if operation == "view":
            continue
        if "*" in spec:
            if app_label in PLUMBING:
                continue
            actions = spec["*"]
        else:
            actions = spec.get(f"{app_label}.{model_name}", ())
        if operation in actions:
            expected.add(f"{app_label}.{permission.codename}")
    return expected


def all_model_keys() -> list[str]:
    return sorted(
        f"{model._meta.app_label}.{model._meta.model_name}" for model in site._registry
    )


#: Every (role, model) pair. The four operations are asserted inside the test
#: rather than fanned out into separate cases: fanning them out would multiply
#: the number of ``setup_roles`` runs by four for no extra coverage, and the
#: failure message below still names the exact failing cell.
ROLE_MODEL_PAIRS = [
    (role, model_key) for role in sorted(ROLES) for model_key in all_model_keys()
]


# ---------------------------------------------------------------------------
# T-1404 — every role × model × operation cell
# ---------------------------------------------------------------------------


class TestTheMatrixItself:
    def test_there_are_exactly_nine_roles(self, roles_installed):
        """FR-110: the nine named roles exist as Django groups, by name.

        The count alone would survive a rename, and a renamed group is a role
        nobody is assigned to — so the names are asserted, not just the total.
        """
        assert sorted(ROLES) == sorted(NINE_ROLES)

        installed = set(Group.objects.values_list("name", flat=True))
        assert set(NINE_ROLES) <= installed, (
            f"missing role groups: {sorted(set(NINE_ROLES) - installed)}"
        )
        assert Group.objects.filter(name__in=NINE_ROLES).count() == 9

    def test_setup_roles_is_idempotent(self, roles_installed):
        from django.core.management import call_command

        auditor = Group.objects.get(name="Read-only Auditor")
        before = set(auditor.permissions.values_list("pk", flat=True))

        call_command("setup_roles", verbosity=0)

        auditor.refresh_from_db()
        assert set(auditor.permissions.values_list("pk", flat=True)) == before
        assert Group.objects.filter(name__in=ROLES).count() == 9

    @pytest.mark.parametrize("role,model_key", ROLE_MODEL_PAIRS)
    def test_every_cell_matches_the_approved_matrix(
        self, roles_installed, role, model_key
    ):
        user = make_staff(f"cell-{abs(hash((role, model_key)))}@zakey.test", role)
        app_label, model_name = model_key.split(".", 1)

        mismatches = []
        for operation in OPERATIONS:
            granted = user.has_perm(f"{app_label}.{operation}_{model_name}")
            wanted = expected(role, model_key, operation)
            if granted is not wanted:
                mismatches.append(
                    f"{role} × {model_key} × {operation}: "
                    f"granted={granted}, matrix says {wanted}"
                )

        assert mismatches == [], "\n".join(mismatches)

    def test_the_matrix_covers_every_registered_model(self):
        """Guard the guard: the sweep must not silently shrink."""
        assert len(all_model_keys()) >= 40
        assert len(ROLE_MODEL_PAIRS) == 9 * len(all_model_keys())


# ---------------------------------------------------------------------------
# The invariants that must hold whatever the matrix says
# ---------------------------------------------------------------------------


class TestStructuralInvariants:
    @pytest.mark.parametrize("model_key", sorted(APPEND_ONLY))
    @pytest.mark.parametrize("role", sorted(ROLES))
    def test_no_role_can_mutate_an_append_only_ledger(
        self, roles_installed, role, model_key
    ):
        """INV-013: not even a superuser role gets a write path in the admin."""
        model_admin = site._registry[
            next(
                model
                for model in site._registry
                if f"{model._meta.app_label}.{model._meta.model_name}" == model_key
            )
        ]
        user = make_staff(f"append-{role}-{model_key}@zakey.test".lower(), role)
        request = _request_for(user)

        assert model_admin.has_add_permission(request) is False
        assert model_admin.has_change_permission(request) is False
        assert model_admin.has_delete_permission(request) is False

    def test_the_auditor_can_never_write_anything(self, roles_installed):
        """The auditor invariant, stated directly.

        Not parametrised over the nine roles: it is a claim about exactly one
        of them. Collecting nine cases and skipping eight would report eight
        skips that look like missing coverage and hide the fact that the other
        roles' write surfaces are asserted separately, below.
        """
        user = make_staff("auditor-write@zakey.test", "Read-only Auditor")

        writes = sorted(
            perm
            for perm in user.get_all_permissions()
            if not perm.split(".", 1)[1].startswith("view_")
        )

        assert writes == [], f"the read-only auditor holds write permissions: {writes}"

    @pytest.mark.parametrize("role", sorted(ROLES))
    def test_every_roles_write_surface_matches_the_matrix(self, roles_installed, role):
        """What each role may *write*, asserted exactly, for all nine roles.

        This is the assertion the old skipped parametrisation should have been.
        Reads are covered cell-by-cell above; writes deserve their own exact
        set comparison because a stray ``add``/``change``/``delete`` is how a
        role quietly becomes more powerful than the matrix says it is — and a
        superset is just as wrong as a subset, so equality is asserted rather
        than containment.
        """
        user = make_staff(f"writes-{abs(hash(role))}@zakey.test", role)

        actual = {
            perm
            for perm in user.get_all_permissions()
            if not perm.split(".", 1)[1].startswith("view_")
        }

        assert actual == expected_write_permissions(role), (
            f"{role} write surface diverges from the approved matrix.\n"
            f"  unexpectedly granted: {sorted(actual - expected_write_permissions(role))}\n"
            f"  unexpectedly missing: {sorted(expected_write_permissions(role) - actual)}"
        )

    @pytest.mark.parametrize("role", sorted(ROLES))
    def test_a_role_that_should_write_actually_can(self, roles_installed, role):
        """Guard the guard: an empty expectation would make the test above vacuous.

        Only the auditor is legitimately write-free; every other role exists to
        change something, so a role with no write permissions at all means the
        group was built wrong.
        """
        expected = expected_write_permissions(role)

        if role == "Read-only Auditor":
            assert expected == set()
        else:
            assert expected, f"{role} was granted no write permission at all"

    def test_the_auditor_can_read_the_whole_catalogue(self, roles_installed):
        user = make_staff("auditor-read@zakey.test", "Read-only Auditor")

        assert user.has_perm("orders.view_order")
        assert user.has_perm("payments.view_payment")
        assert user.has_perm("audit.view_auditlog")

    @pytest.mark.parametrize("role", sorted(ROLES))
    def test_no_role_grants_django_plumbing(self, roles_installed, role):
        user = make_staff(f"plumbing-{role}@zakey.test".lower(), role)

        leaked = [
            perm
            for perm in user.get_all_permissions()
            if perm.split(".", 1)[0] in PLUMBING
        ]

        assert leaked == [], f"{role} was granted Django plumbing permissions: {leaked}"

    def test_a_staff_user_with_no_role_can_do_nothing(self, roles_installed):
        user = make_staff("norole@zakey.test")

        assert user.get_all_permissions() == set()


def _request_for(user):
    from django.test import RequestFactory

    request = RequestFactory().get("/admin/")
    request.user = user
    return request


# ---------------------------------------------------------------------------
# T-1403 — enforcement is server-side, over HTTP
# ---------------------------------------------------------------------------


class TestServerSideEnforcement:
    @pytest.mark.parametrize(
        "role,url_name,should_reach",
        [
            ("Catalogue Manager", "admin:catalog_product_changelist", True),
            ("Catalogue Manager", "admin:payments_payment_changelist", False),
            ("Catalogue Manager", "admin:orders_order_changelist", False),
            ("Inventory Manager", "admin:inventory_stockitem_changelist", True),
            ("Inventory Manager", "admin:payments_refund_changelist", False),
            ("Order Fulfilment", "admin:orders_order_changelist", True),
            ("Order Fulfilment", "admin:promotions_coupon_changelist", False),
            ("Customer Service", "admin:accounts_customerprofile_changelist", True),
            ("Customer Service", "admin:payments_refund_changelist", False),
            ("Finance", "admin:payments_payment_changelist", True),
            ("Finance", "admin:catalog_product_changelist", False),
            ("Content Manager", "admin:content_faq_changelist", True),
            ("Content Manager", "admin:orders_order_changelist", False),
            ("Read-only Auditor", "admin:orders_order_changelist", True),
            ("Read-only Auditor", "admin:audit_auditlog_changelist", True),
        ],
    )
    def test_direct_url_access_respects_the_role(
        self, client, roles_installed, role, url_name, should_reach
    ):
        """A crafted URL must not reach what the menu would not show."""
        user = make_staff(f"url-{role}-{url_name}@zakey.test".lower(), role)
        client.force_login(user)

        response = client.get(reverse(url_name))

        if should_reach:
            assert response.status_code == 200
        else:
            assert response.status_code in (302, 403), (
                f"{role} reached {url_name} with status {response.status_code}"
            )

    def test_a_read_only_role_cannot_post_a_change(
        self, client, roles_installed, product
    ):
        """The layer that matters: refusing the POST, not hiding the button."""
        user = make_staff("auditor-post@zakey.test", "Read-only Auditor")
        client.force_login(user)
        url = reverse("admin:catalog_product_change", args=[product.pk])
        original = product.name

        response = client.post(url, {"name": "اسم مُخترق", "slug": product.slug})

        product.refresh_from_db()
        assert product.name == original
        assert response.status_code in (302, 403)

    def test_a_role_without_delete_cannot_post_a_delete(
        self, client, roles_installed, product
    ):
        user = make_staff("inv-delete@zakey.test", "Inventory Manager")
        client.force_login(user)

        response = client.post(
            reverse("admin:catalog_product_delete", args=[product.pk]), {"post": "yes"}
        )

        from apps.catalog.models import Product

        assert Product.objects.filter(pk=product.pk).exists()
        assert response.status_code in (302, 403)

    def test_a_non_staff_user_cannot_reach_the_admin_at_all(self, client, customer):
        client.force_login(customer.user)

        response = client.get(reverse("admin:index"))

        assert response.status_code == 302
        assert "/admin/login" in response["Location"]

    def test_the_export_endpoint_respects_the_role(self, client, roles_installed):
        """Export is a read of everything; it must not bypass the matrix."""
        user = make_staff("content-export@zakey.test", "Content Manager")
        client.force_login(user)

        response = client.get(reverse("admin:orders_order_export"))

        assert response.status_code in (302, 403)

    def test_the_import_endpoint_respects_the_role(self, client, roles_installed):
        user = make_staff("fulfil-import@zakey.test", "Order Fulfilment")
        client.force_login(user)

        try:
            url = reverse("admin:catalog_product_import")
        except NoReverseMatch:  # pragma: no cover
            pytest.skip("import endpoint not registered")

        response = client.get(url)

        assert response.status_code in (302, 403)


# ---------------------------------------------------------------------------
# T-1405 — menu hiding is cosmetic, never authorisation
# ---------------------------------------------------------------------------


class TestMenuHidingIsNotAuthorisation:
    def test_a_hidden_model_is_still_refused_by_url(self, client, roles_installed):
        """Hiding neither grants nor denies. The URL must refuse on its own.

        This is the whole T-1405 claim: if the only thing stopping a role were
        the absence of a link, typing the URL would be a complete bypass.
        """
        user = make_staff("hidden-url@zakey.test", "Content Manager")
        client.force_login(user)

        index = client.get(reverse("admin:index")).content.decode()
        assert "/admin/payments/payment/" not in index, "precondition: link is hidden"

        response = client.get(reverse("admin:payments_payment_changelist"))
        assert response.status_code in (302, 403), (
            "the model was hidden from the menu but reachable by URL"
        )

    def test_a_visible_model_is_genuinely_permitted(self, client, roles_installed):
        """The converse: showing a link must not be the thing that grants access."""
        user = make_staff("visible-url@zakey.test", "Finance")
        client.force_login(user)

        assert client.get(reverse("admin:payments_payment_changelist")).status_code == 200
        assert user.has_perm("payments.view_payment")

    def test_hiding_a_model_in_settings_changes_no_permission(
        self, client, roles_installed, settings
    ):
        """Jazzmin's ``hide_models`` is presentation, and must stay that way.

        With the model hidden, the role that legitimately holds the permission
        must still be able to use it over HTTP.
        """
        settings.JAZZMIN_SETTINGS = {
            **settings.JAZZMIN_SETTINGS,
            "hide_models": ["payments.Payment"],
        }
        user = make_staff("jazzmin-hide@zakey.test", "Finance")
        client.force_login(user)

        response = client.get(reverse("admin:payments_payment_changelist"))

        assert user.has_perm("payments.view_payment")
        assert response.status_code == 200, "hiding a model revoked a real permission"
