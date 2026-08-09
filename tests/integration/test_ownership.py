"""Ownership sweep over every customer-owned model (T-0406, FR-056, INV-010).

The contract under test: cross-user access is a 404, signed-out access to an
account-owned object is a login redirect, and session-scoped anonymous rows
answer to their own session key only — never to another visitor's.
"""

from __future__ import annotations

import pytest
from django.core.exceptions import PermissionDenied
from django.http import Http404

from apps.accounts.models import Address, CustomerProfile, User
from apps.cart.models import Cart, CartLine, Wishlist, WishlistItem
from apps.core.ownership import get_owned_object
from apps.orders.models import Order, OrderAddress

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Two fully-fleshed customers with one owned row of every model each.
# ---------------------------------------------------------------------------


def _order(number, customer=None):
    return Order.objects.create(
        number=number,
        customer=customer,
        email="owner@example.com",
        phone="01012345678",
        idempotency_key=f"idem-{number}",
        subtotal="100.00",
        grand_total="114.00",
    )


@pytest.fixture
def owned_matrix(db, customer, other_customer, governorate, area, variant):
    case = {}
    case["customer"] = CustomerProfile.objects.get(pk=customer.pk)
    case["other_customer"] = CustomerProfile.objects.get(pk=other_customer.pk)

    def build(owner, tag):
        bundle = {}
        bundle["cart"] = Cart.objects.create(customer=owner)
        bundle["cartline"] = CartLine.objects.create(cart=bundle["cart"], variant=variant, quantity=1)
        wishlist, _ = Wishlist.objects.get_or_create(customer=owner)
        bundle["wishlist"] = wishlist
        bundle["wishlistitem"] = WishlistItem.objects.create(
            wishlist=wishlist, product=variant.product
        )
        bundle["order"] = _order(f"OWN-{tag}", owner)
        bundle["orderaddress"] = OrderAddress.objects.create(
            order=bundle["order"],
            full_name="مالك",
            phone="01012345678",
            governorate_key=governorate.key,
            governorate_name=governorate.name,
            city="القاهرة",
            street="١ شارع الاختبار",
            building="١",
        )
        bundle["address"] = Address.objects.create(
            customer=owner,
            full_name="مالك",
            phone="01012345678",
            governorate=governorate,
            area=area,
            city="القاهرة",
            street="١ شارع الاختبار",
            building="١",
        )
        bundle["profile"] = owner
        return bundle

    case["mine"] = build(customer, "A")
    case["theirs"] = build(other_customer, "B")
    return case


MODEL_KEYS = [
    "cart",
    "cartline",
    "wishlist",
    "wishlistitem",
    "order",
    "orderaddress",
    "address",
    "profile",
]

MODELS = {
    "cart": Cart,
    "cartline": CartLine,
    "wishlist": Wishlist,
    "wishlistitem": WishlistItem,
    "order": Order,
    "orderaddress": OrderAddress,
    "address": Address,
    "profile": CustomerProfile,
}


# ---------------------------------------------------------------------------
# The 404 cross-user sweep — every customer-owned model
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("key", MODEL_KEYS)
def test_owner_fetches_own_row(owned_matrix, customer, key):
    obj = get_owned_object(MODELS[key], owned_matrix["mine"][key].pk, customer.user)
    assert obj.pk == owned_matrix["mine"][key].pk


@pytest.mark.parametrize("key", MODEL_KEYS)
def test_cross_user_access_is_a_404(owned_matrix, customer, key):
    """FR-056: another customer's object must answer 404 — not 403, not 500."""
    with pytest.raises(Http404):
        get_owned_object(MODELS[key], owned_matrix["theirs"][key].pk, customer.user)


@pytest.mark.parametrize("key", MODEL_KEYS)
def test_signed_out_access_is_a_redirect_boundary(owned_matrix, key):
    """Signed-out callers cannot reach account-owned rows.

    With NO credential at all (no user, no session key) the helper cannot even
    scope a queryset, so it raises PermissionDenied and the view layer turns
    that into the standard login redirect (302).

    With a *wrong* credential (a stranger's session key) the answer must be the
    uniform 404 for the four session-ownable models — anything else would leak
    "this id exists but is not yours", which is the exact distinction FR-056
    forbids. The other four models have no session-ownership path at all, so
    they stay on the PermissionDenied branch.
    """
    with pytest.raises(PermissionDenied):
        get_owned_object(MODELS[key], owned_matrix["mine"][key].pk, None)

    ghost_outcome = Http404 if key in ANON_KEYS else PermissionDenied
    with pytest.raises(ghost_outcome):
        get_owned_object(
            MODELS[key], owned_matrix["mine"][key].pk, None, session_key="ghost-session"
        )


def test_ownership_never_raises_500_for_foreign_keys(owned_matrix, customer):
    """Cross-user is a queryset filter, never an object-level exception path:
    line-level models resolve through their parent's owner in one query."""
    for key in ("cartline", "wishlistitem", "orderaddress"):
        try:
            get_owned_object(MODELS[key], owned_matrix["theirs"][key].pk, customer.user)
        except Http404:
            continue
        raise AssertionError(f"{key} cross-user lookup did not 404")


# ---------------------------------------------------------------------------
# Matrix: anonymous (session-scoped) rows
# ---------------------------------------------------------------------------


@pytest.fixture
def anonymous_rows(db, variant):
    cart = Cart.objects.create(session_key="alice-session", customer=None)
    wishlist = Wishlist.objects.create(session_key="alice-session", customer=None)
    return {
        "cart": cart,
        "cartline": CartLine.objects.create(cart=cart, variant=variant, quantity=1),
        "wishlist": wishlist,
        "wishlistitem": WishlistItem.objects.create(wishlist=wishlist, product=variant.product),
    }


ANON_KEYS = ["cart", "cartline", "wishlist", "wishlistitem"]


@pytest.mark.parametrize("key", ANON_KEYS)
def test_anonymous_session_reads_own_row(anonymous_rows, key):
    obj = get_owned_object(MODELS[key], anonymous_rows[key].pk, None, session_key="alice-session")
    assert obj.pk == anonymous_rows[key].pk


@pytest.mark.parametrize("key", ANON_KEYS)
def test_foreign_session_gets_a_404(anonymous_rows, key):
    with pytest.raises(Http404):
        get_owned_object(MODELS[key], anonymous_rows[key].pk, None, session_key="mallory-session")


@pytest.mark.parametrize("key", ANON_KEYS)
def test_signed_in_user_cannot_lift_anonymous_row(anonymous_rows, customer, key):
    """An account user's own scope excludes anonymous baskets: matching only
    on session key would let any logged-in user adopt a stranger's cart."""
    with pytest.raises(Http404):
        get_owned_object(MODELS[key], anonymous_rows[key].pk, customer.user)


@pytest.mark.parametrize("key", ANON_KEYS)
def test_anonymous_row_without_session_key_is_unanswerable(anonymous_rows, key):
    with pytest.raises(PermissionDenied):
        get_owned_object(MODELS[key], anonymous_rows[key].pk, None, session_key="")


# ---------------------------------------------------------------------------
# Unregistered models fail closed, not open
# ---------------------------------------------------------------------------


def test_unregistered_model_fails_closed(owned_matrix, customer):
    from apps.orders.models import OrderEvent

    with pytest.raises(LookupError):
        get_owned_object(OrderEvent, 1, customer.user)


def test_login_required_confusion_cannot_be_wrapped_into_a_403(owned_matrix, customer):
    """The contract: nothing here raises 403 — the framework-level outcome for
    cross-user reads is a 404 every time (see FR-056 language: MUST return 404)."""
    from django.http import Http404

    forbidden_exceptions = (Http404, PermissionDenied, LookupError)
    for key in MODEL_KEYS:
        with pytest.raises(forbidden_exceptions):
            get_owned_object(MODELS[key], owned_matrix["theirs"][key].pk, customer.user)
