"""Account, authentication and ownership over HTTP (T-1606, FR-050 – FR-057).

The prototype rendered a fabricated customer whenever the URL said
``?state=signed-in``. These tests assert the replacement: identity comes from
the session, the anonymous basket follows the visitor into their account, and
one customer cannot see or touch another's data.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import Address, CustomerProfile, User
from apps.cart.models import Cart, CartStatus
from apps.catalog.models import Product

pytestmark = pytest.mark.django_db

PASSWORD = "Zakey-Pass!123"


@pytest.fixture
def registered(db):
    user = User.objects.create_user(email="nada@example.com", password=PASSWORD)
    profile = CustomerProfile.objects.create(
        user=user, full_name="ندى إبراهيم", phone="01012345678"
    )
    return user, profile


def _login(client, email="nada@example.com", password=PASSWORD):
    return client.post(
        reverse("storefront:account-login"), {"email": email, "password": password}, follow=True
    )


# ---------------------------------------------------------------------------
# Identity comes from the session, not the URL
# ---------------------------------------------------------------------------


def test_signed_out_visitor_sees_the_auth_forms(storefront):
    response = storefront.get(reverse("storefront:account"))
    assert response.context["account_mode"] == "signed-out"
    assert "الطلبات" not in response.content.decode() or "تسجيل الدخول" in response.content.decode()


def test_state_query_parameter_no_longer_grants_a_session(storefront):
    """The prototype's ``?state=signed-in`` switch must be inert."""
    response = storefront.get(reverse("storefront:account"), {"state": "signed-in"})
    assert response.context["account_mode"] == "signed-out"


def test_login_signs_the_customer_in(storefront, registered):
    response = _login(storefront)
    assert response.context["account_mode"] == "signed-in"
    assert response.context["profile"].full_name == "ندى إبراهيم"


def test_wrong_password_does_not_sign_in(storefront, registered):
    response = _login(storefront, password="not-the-password")
    assert response.context["account_mode"] == "signed-out"


def test_logout_ends_the_session(storefront, registered):
    _login(storefront)
    storefront.post(reverse("storefront:account-logout"), follow=True)
    assert storefront.get(reverse("storefront:account")).context["account_mode"] == "signed-out"


def test_registration_creates_a_real_account(storefront):
    storefront.post(
        reverse("storefront:account-register"),
        {
            "full_name": "سلمى عادل",
            "email": "salma@example.com",
            "mobile": "01112345678",
            "password": PASSWORD,
            "password_confirm": PASSWORD,
        },
        follow=True,
    )
    user = User.objects.get(email="salma@example.com")
    assert user.customer_profile.full_name == "سلمى عادل"
    # Never storable from a storefront form (FR-057).
    assert user.is_staff is False and user.is_superuser is False


# ---------------------------------------------------------------------------
# The anonymous basket follows the visitor in (FR-032)
# ---------------------------------------------------------------------------


def test_anonymous_cart_merges_into_the_account_on_login(storefront, registered):
    variant = Product.objects.get(slug="zakey-apex-pro").variants.first()
    storefront.post(
        reverse("storefront:cart-add"), {"variant": variant.pk, "quantity": 2}, follow=True
    )
    assert Cart.objects.filter(customer__isnull=True).exists()

    _login(storefront)

    _, profile = registered
    account_cart = Cart.objects.get(customer=profile, status=CartStatus.ACTIVE)
    assert account_cart.lines.get(variant=variant).quantity == 2
    assert not Cart.objects.filter(
        customer__isnull=True, status=CartStatus.ACTIVE
    ).exists(), "the anonymous cart was left active after merging"


def test_anonymous_wishlist_merges_on_login(storefront, registered):
    product = Product.objects.get(slug="zakey-apex-pro")
    storefront.post(reverse("storefront:wishlist-toggle"), {"product": product.pk}, follow=True)

    _login(storefront)

    _, profile = registered
    assert profile.wishlist.items.filter(product=product).exists()


# ---------------------------------------------------------------------------
# Addresses (FR-055, INV-014)
# ---------------------------------------------------------------------------


ADDRESS = {
    "full_name": "ندى إبراهيم",
    "phone": "01012345678",
    "governorate": "cairo",
    "city": "القاهرة",
    "street": "١٢ شارع التحرير",
    "building": "٥",
}


def test_customer_can_add_an_address(storefront, registered):
    _login(storefront)
    storefront.post(reverse("storefront:address-create"), ADDRESS, follow=True)

    _, profile = registered
    address = profile.addresses.get()
    assert address.city == "القاهرة"
    # The first address is the default, without being asked for.
    assert address.is_default is True


def test_only_one_address_stays_default(storefront, registered):
    _login(storefront)
    storefront.post(reverse("storefront:address-create"), ADDRESS, follow=True)
    storefront.post(
        reverse("storefront:address-create"),
        {**ADDRESS, "city": "الجيزة", "is_default": "1"},
        follow=True,
    )

    _, profile = registered
    assert profile.addresses.filter(is_default=True).count() == 1
    assert profile.addresses.get(is_default=True).city == "الجيزة"


def test_customer_cannot_delete_another_customers_address(storefront, registered, db):
    from apps.shipping.models import Governorate

    other_user = User.objects.create_user(email="omar@example.com", password=PASSWORD)
    other = CustomerProfile.objects.create(
        user=other_user, full_name="عمر حسن", phone="01112345678"
    )
    victim_address = Address.objects.create(
        customer=other,
        full_name="عمر حسن",
        phone="01112345678",
        governorate=Governorate.objects.get(key="cairo"),
        city="القاهرة",
        street="٣ شارع آخر",
        building="٢",
    )

    _login(storefront)
    response = storefront.post(
        reverse("storefront:address-delete"), {"address": victim_address.pk}
    )

    assert response.status_code == 404
    assert Address.objects.filter(pk=victim_address.pk).exists()


# ---------------------------------------------------------------------------
# Profile (FR-057)
# ---------------------------------------------------------------------------


def test_customer_can_update_their_profile(storefront, registered):
    _login(storefront)
    storefront.post(
        reverse("storefront:profile-update"),
        {"full_name": "ندى إبراهيم علي", "phone": "01212345678"},
        follow=True,
    )
    _, profile = registered
    profile.refresh_from_db()
    assert profile.full_name == "ندى إبراهيم علي"
    assert profile.phone == "01212345678"


def test_profile_update_cannot_escalate_privileges(storefront, registered):
    user, _ = registered
    _login(storefront)
    storefront.post(
        reverse("storefront:profile-update"),
        {
            "full_name": "ندى إبراهيم",
            "phone": "01012345678",
            "is_staff": "true",
            "is_superuser": "true",
        },
        follow=True,
    )
    user.refresh_from_db()
    assert user.is_staff is False and user.is_superuser is False


# ---------------------------------------------------------------------------
# Order history is scoped to the owner (FR-056, INV-010)
# ---------------------------------------------------------------------------


def test_order_history_shows_only_your_own_orders(storefront, registered):
    from apps.orders.models import Order

    _, profile = registered
    other_user = User.objects.create_user(email="omar@example.com", password=PASSWORD)
    other = CustomerProfile.objects.create(
        user=other_user, full_name="عمر حسن", phone="01112345678"
    )
    mine = Order.objects.create(
        number="ZK-MINE", customer=profile, email="nada@example.com",
        phone="01012345678", idempotency_key="k-mine",
        subtotal="100.00", grand_total="114.00",
    )
    theirs = Order.objects.create(
        number="ZK-THEIRS", customer=other, email="omar@example.com",
        phone="01112345678", idempotency_key="k-theirs",
        subtotal="100.00", grand_total="114.00",
    )

    _login(storefront)
    body = storefront.get(reverse("storefront:account"), {"tab": "orders"}).content.decode()
    assert mine.number in body
    assert theirs.number not in body


def test_mutating_account_endpoints_reject_get(storefront):
    for route in (
        "storefront:account-login",
        "storefront:account-register",
        "storefront:account-logout",
        "storefront:address-create",
        "storefront:address-delete",
        "storefront:profile-update",
    ):
        assert storefront.get(reverse(route)).status_code == 405, route
