"""Server-side cart, wishlist and coupon behaviour (T-1604, FR-030 – FR-040).

These are the tests the prototype could not have: they drive the real HTTP
endpoints and assert that the *database* changed, that the totals the page shows
were computed on the server, and that a hostile request body cannot move money.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.cart.models import Cart, CartLine, Wishlist
from apps.catalog.models import Product, ProductVariant

pytestmark = pytest.mark.django_db


def _variants(slug="zakey-apex-pro"):
    product = Product.objects.get(slug=slug)
    return list(product.variants.order_by("position", "id"))


def _add(client, variant, quantity=1, **extra):
    return client.post(
        reverse("storefront:cart-add"),
        {"variant": variant.pk, "quantity": quantity, **extra},
        follow=True,
    )


# ---------------------------------------------------------------------------
# The line-identity defect the prototype had (store.js:34,41)
# ---------------------------------------------------------------------------


def test_two_finishes_of_one_product_are_independent_lines(storefront):
    first, second = _variants()[:2]
    _add(storefront, first, 2)
    _add(storefront, second, 3)

    cart = Cart.objects.get()
    assert cart.lines.count() == 2, "two finishes collapsed into one line"

    # Updating one finish must not touch the other.
    storefront.post(
        reverse("storefront:cart-update"), {"variant": first.pk, "quantity": 5}, follow=True
    )
    assert CartLine.objects.get(cart=cart, variant=first).quantity == 5
    assert CartLine.objects.get(cart=cart, variant=second).quantity == 3

    # …and removing one leaves the other alone.
    storefront.post(reverse("storefront:cart-remove"), {"variant": first.pk}, follow=True)
    assert not CartLine.objects.filter(cart=cart, variant=first).exists()
    assert CartLine.objects.filter(cart=cart, variant=second).exists()


def test_adding_the_same_variant_twice_increases_one_line(storefront):
    variant = _variants()[0]
    _add(storefront, variant, 2)
    _add(storefront, variant, 3)

    line = CartLine.objects.get()
    assert line.quantity == 5


def test_quantity_zero_removes_the_line(storefront):
    variant = _variants()[0]
    _add(storefront, variant, 2)
    storefront.post(
        reverse("storefront:cart-update"), {"variant": variant.pk, "quantity": 0}, follow=True
    )
    assert not CartLine.objects.exists()


# ---------------------------------------------------------------------------
# The browser is not trusted for money (FR-034, threat T-03)
# ---------------------------------------------------------------------------


def test_posted_money_fields_are_ignored(storefront):
    """A tampered body carries prices; the server prices from its own rows."""
    variant = _variants()[0]
    _add(
        storefront,
        variant,
        1,
        price="1",
        unit_price="1",
        total="1",
        subtotal="1",
        discount="9999",
        vat="0",
        grand_total="1",
    )

    response = storefront.get(reverse("storefront:cart"))
    totals = response.context["cart_totals"]
    assert totals.subtotal == variant.price
    assert totals.discount_total == Decimal("0.00")
    assert totals.grand_total == variant.price


def test_quantity_is_clamped_to_the_configured_maximum(storefront, site_setting):
    variant = _variants()[0]
    _add(storefront, variant, 99)
    assert CartLine.objects.get().quantity <= site_setting.max_line_quantity


def test_vat_is_extracted_not_added(storefront):
    """Catalogue prices are VAT-inclusive, so VAT comes out of the total."""
    variant = _variants()[0]
    _add(storefront, variant, 1)

    totals = storefront.get(reverse("storefront:cart")).context["cart_totals"]
    assert totals.grand_total == variant.price, "VAT was added on top of a gross price"
    expected = (variant.price * totals.vat_rate / (1 + totals.vat_rate)).quantize(
        Decimal("0.01")
    )
    assert abs(totals.vat_amount - expected) <= Decimal("0.01")


# ---------------------------------------------------------------------------
# Coupons are validated server-side (FR-082)
# ---------------------------------------------------------------------------


def test_unknown_coupon_is_rejected_and_changes_nothing(storefront):
    _add(storefront, _variants()[0], 1)
    storefront.post(
        reverse("storefront:cart-coupon"), {"coupon": "NOT-A-REAL-CODE"}, follow=True
    )

    cart = Cart.objects.get()
    assert cart.coupon is None
    assert storefront.get(reverse("storefront:cart")).context[
        "cart_totals"
    ].discount_total == Decimal("0.00")


def test_seeded_demo_coupon_applies_a_server_computed_discount(storefront):
    from apps.promotions.models import Coupon

    coupon = Coupon.objects.filter(is_active=True).first()
    if coupon is None:
        pytest.skip("no active coupon seeded")

    _add(storefront, _variants()[0], 1)
    storefront.post(
        reverse("storefront:cart-coupon"), {"coupon": coupon.code.lower()}, follow=True
    )

    totals = storefront.get(reverse("storefront:cart")).context["cart_totals"]
    assert Cart.objects.get().coupon_id == coupon.pk
    assert totals.discount_total > Decimal("0.00")
    assert totals.grand_total == totals.subtotal - totals.discount_total


# ---------------------------------------------------------------------------
# Endpoints refuse GET and require CSRF (FR-039, threat T-05)
# ---------------------------------------------------------------------------


MUTATING_ROUTES = [
    "storefront:cart-add",
    "storefront:cart-update",
    "storefront:cart-remove",
    "storefront:cart-coupon",
    "storefront:wishlist-toggle",
    "storefront:newsletter",
]


@pytest.mark.parametrize("route", MUTATING_ROUTES)
def test_mutating_endpoints_reject_get(storefront, route):
    assert storefront.get(reverse(route)).status_code == 405


@pytest.mark.parametrize("route", MUTATING_ROUTES)
def test_mutating_endpoints_require_csrf(seeded_catalogue, route):
    from django.test import Client

    unsafe = Client(enforce_csrf_checks=True)
    assert unsafe.post(reverse(route), {}).status_code == 403


# ---------------------------------------------------------------------------
# Wishlist persists to the database, not to localStorage (FR-037)
# ---------------------------------------------------------------------------


def test_wishlist_toggle_persists_and_reverses(storefront):
    product = Product.objects.get(slug="zakey-apex-pro")
    url = reverse("storefront:wishlist-toggle")

    storefront.post(url, {"product": product.pk}, follow=True)
    assert Wishlist.objects.get().items.filter(product=product).exists()

    storefront.post(url, {"product": product.pk}, follow=True)
    assert not Wishlist.objects.get().items.filter(product=product).exists()


def test_wishlist_page_renders_saved_products_server_side(storefront):
    product = Product.objects.get(slug="zakey-apex-pro")
    storefront.post(reverse("storefront:wishlist-toggle"), {"product": product.pk}, follow=True)

    response = storefront.get(reverse("storefront:wishlist"))
    assert response.context["wishlist_count"] == 1
    assert product.name in response.content.decode()


def test_unpublished_product_cannot_be_added(storefront):
    from apps.core.models import PublicationStatus

    product = Product.objects.get(slug="zakey-apex-pro")
    product.status = PublicationStatus.DRAFT
    product.save(update_fields=["status"])

    _add(storefront, product.variants.first(), 1)
    assert not CartLine.objects.exists()


def test_unknown_variant_is_rejected(storefront):
    missing = ProductVariant.objects.order_by("-pk").first().pk + 1000
    storefront.post(
        reverse("storefront:cart-add"), {"variant": missing, "quantity": 1}, follow=True
    )
    assert not CartLine.objects.exists()


# ---------------------------------------------------------------------------
# The cart survives a page load without JavaScript (FR-136)
# ---------------------------------------------------------------------------


def test_cart_page_renders_lines_without_any_javascript(storefront):
    variant = _variants()[0]
    _add(storefront, variant, 2)

    body = storefront.get(reverse("storefront:cart")).content.decode()
    assert variant.product.name in body, "cart lines are not in the served HTML"
    assert 'data-cart-line' in body
    # The summary figures must be in the markup, not computed after load.
    assert "data-cart-subtotal" in body and "data-cart-total" in body


def test_header_badge_counts_come_from_the_server(storefront):
    _add(storefront, _variants()[0], 3)
    response = storefront.get(reverse("storefront:home"))
    assert response.context["cart_count"] == 3
