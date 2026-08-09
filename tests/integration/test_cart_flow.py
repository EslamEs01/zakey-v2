"""Server-side cart, wishlist and coupon behaviour (T-1604, FR-030 – FR-040).

These are the tests the prototype could not have: they drive the real HTTP
endpoints and assert that the *database* changed, that the totals the page shows
were computed on the server, and that a hostile request body cannot move money.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

from apps.cart.models import Cart, CartLine, CartStatus, Wishlist
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
    """A tampered body carries prices; the server prices from its own rows (FR-034)."""
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
    """Every cart and wishlist mutation is POST-only; a GET is refused (FR-039)."""
    assert storefront.get(reverse(route)).status_code == 405


@pytest.mark.parametrize("route", MUTATING_ROUTES)
def test_mutating_endpoints_require_csrf(seeded_catalogue, route):
    """Every cart and wishlist mutation refuses a POST with no token (FR-039)."""
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


# ---------------------------------------------------------------------------
# Whose basket is it, and what happens when the two meet (FR-031, FR-032)
# ---------------------------------------------------------------------------


PASSWORD = "StrongPass!234"  # the password the ``user`` fixture registers with


def _login(client, email="nada@example.com", password=PASSWORD):
    return client.post(
        reverse("storefront:account-login"),
        {"email": email, "password": password},
        follow=True,
    )


def _account_line(customer):
    """The single line of the customer's live cart."""
    return CartLine.objects.get(cart__customer=customer, cart__status=CartStatus.ACTIVE)


def test_an_anonymous_basket_belongs_to_one_session_only(storefront):
    """An anonymous cart is bound to the visitor's session key (FR-031).

    Two visitors share one server, so the only thing separating their baskets is
    the session that owns the row.
    """
    variant = _variants()[0]
    _add(storefront, variant, 2)

    cart = Cart.objects.get()
    assert cart.customer_id is None
    assert cart.session_key == storefront.session.session_key

    stranger = Client()
    assert stranger.get(reverse("storefront:cart")).context["cart_count"] == 0
    assert storefront.get(reverse("storefront:cart")).context["cart_count"] == 2


def test_a_signed_in_basket_persists_into_the_next_session(storefront, customer):
    """A customer's cart is persistent, not session-bound (FR-031).

    The row is owned by the account, so a new browser on another day finds the
    same basket rather than an empty one.
    """
    variant = _variants()[0]
    _login(storefront)
    _add(storefront, variant, 2)

    cart = Cart.objects.get(customer=customer, status=CartStatus.ACTIVE)
    assert cart.session_key == "", "an account cart was pinned to one session"

    tomorrow = Client()  # a different browser, a brand-new session
    _login(tomorrow)

    assert tomorrow.get(reverse("storefront:cart")).context["cart_count"] == 2
    assert Cart.objects.filter(status=CartStatus.ACTIVE).count() == 1


def test_signing_in_sums_the_anonymous_basket_into_the_account_one(storefront, customer):
    """On sign-in the two baskets are added together, not swapped (FR-032)."""
    variant = _variants()[0]

    earlier = Client()
    _login(earlier)
    _add(earlier, variant, 2)  # what the account already held

    _add(storefront, variant, 3)  # what the visitor added before signing in
    _login(storefront)

    assert _account_line(customer).quantity == 5


def test_the_sign_in_merge_clamps_to_the_per_line_maximum(storefront, customer, site_setting):
    """Summing must not push a merged line past the per-line ceiling (FR-032)."""
    variant = _variants()[0]
    maximum = site_setting.max_line_quantity

    earlier = Client()
    _login(earlier)
    _add(earlier, variant, 5)
    _add(storefront, variant, 6)

    _login(storefront)

    assert 5 + 6 > maximum, "the numbers no longer exercise the clamp"
    assert _account_line(customer).quantity == maximum


def test_the_sign_in_merge_clamps_to_available_stock(storefront, customer):
    """A merge may not build a basket the warehouse cannot fill (FR-032)."""
    variant = _variants()[0]

    earlier = Client()
    _login(earlier)
    _add(earlier, variant, 3)
    _add(storefront, variant, 3)

    stock = variant.stock_item
    stock.on_hand = 4
    stock.save(update_fields=["on_hand", "updated_at"])

    _login(storefront)

    assert _account_line(customer).quantity == 4, "the merge sold stock that is not there"


# ---------------------------------------------------------------------------
# A line that went bad is flagged, not deleted (FR-035)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("break_it", ["unpublish", "archive", "sell_out"])
def test_a_line_that_became_unavailable_is_flagged_and_excluded_but_still_shown(
    storefront, break_it
):
    """An unsellable line stays visible, flagged, and out of the totals (FR-035).

    Silently dropping it would be the worst of both worlds: the customer's
    basket changes behind their back and the total moves with no explanation.
    """
    from apps.core.models import PublicationStatus

    good = _variants()[0]
    doomed = _variants("zakey-vision-x")[0]
    _add(storefront, good, 1)
    _add(storefront, doomed, 1)

    if break_it == "unpublish":
        Product.objects.filter(pk=doomed.product_id).update(status=PublicationStatus.DRAFT)
    elif break_it == "archive":
        ProductVariant.objects.filter(pk=doomed.pk).update(is_active=False)
    else:
        stock = doomed.stock_item
        stock.on_hand = 0
        stock.save(update_fields=["on_hand", "updated_at"])

    response = storefront.get(reverse("storefront:cart"))
    totals = response.context["cart_totals"]
    shown = {record["variant_id"]: record for record in response.context["cart_lines"]}

    assert doomed.pk in shown, "the unavailable line vanished from the basket"
    assert shown[doomed.pk]["available"] is False
    assert shown[doomed.pk]["reason"], "the line was set aside without saying why"
    assert [priced.variant.pk for priced in totals.unavailable_lines] == [doomed.pk]
    assert totals.subtotal == good.price, "an unavailable line was still charged for"
    assert totals.grand_total == good.price

    body = response.content.decode()
    assert doomed.product.name in body, "the flagged line is not in the served HTML"
    assert "data-cart-unavailable" in body


# ---------------------------------------------------------------------------
# A repriced variant is repriced in the basket, in front of the customer
# (FR-036)
# ---------------------------------------------------------------------------


def test_a_price_change_since_adding_is_applied_and_shown_before_submission(storefront):
    """The basket reprices to the current price and shows it (FR-036).

    Nothing monetary is stored on a cart line, so the only price that can be
    charged is today's — and both the cart and the checkout review render it
    before anything is submitted.
    """
    variant = _variants()[0]
    _add(storefront, variant, 2)
    stale_total = variant.price * 2

    new_price = variant.price + Decimal("1500.00")
    ProductVariant.objects.filter(pk=variant.pk).update(price=new_price)
    current_total = new_price * 2

    cart_page = storefront.get(reverse("storefront:cart"))
    assert cart_page.context["cart_totals"].subtotal == current_total
    assert cart_page.context["cart_totals"].grand_total == current_total

    cart_body = cart_page.content.decode()
    assert f"{current_total:.0f}" in cart_body, "the customer was shown a stale total"
    assert f"{stale_total:.0f}" not in cart_body

    # …and again on the last page before the order is submitted.
    checkout_page = storefront.get(reverse("storefront:checkout"))
    assert checkout_page.context["cart_totals"].subtotal == current_total
    assert f"{current_total:.0f}" in checkout_page.content.decode()


# ---------------------------------------------------------------------------
# Wishlists belong to the account and survive the session (FR-037)
# ---------------------------------------------------------------------------


def test_a_saved_product_survives_into_a_new_session(storefront, customer):
    """A signed-in customer's wishlist is stored, not remembered by a browser (FR-037)."""
    product = Product.objects.get(slug="zakey-apex-pro")
    _login(storefront)
    storefront.post(reverse("storefront:wishlist-toggle"), {"product": product.pk}, follow=True)

    tomorrow = Client()
    _login(tomorrow)
    response = tomorrow.get(reverse("storefront:wishlist"))

    assert response.context["wishlist_count"] == 1
    assert Wishlist.objects.get(customer=customer).items.filter(product=product).exists()


def test_a_session_wishlist_merges_into_the_account_on_sign_in(storefront, customer):
    """Saving something before signing in keeps it afterwards (FR-037)."""
    saved_before_signing_in = Product.objects.get(slug="zakey-vision-x")
    saved_by_the_account = Product.objects.get(slug="zakey-apex-pro")

    earlier = Client()
    _login(earlier)
    earlier.post(
        reverse("storefront:wishlist-toggle"), {"product": saved_by_the_account.pk}, follow=True
    )

    storefront.post(
        reverse("storefront:wishlist-toggle"),
        {"product": saved_before_signing_in.pk},
        follow=True,
    )
    _login(storefront)

    saved = set(
        Wishlist.objects.get(customer=customer).items.values_list("product_id", flat=True)
    )
    assert saved == {saved_by_the_account.pk, saved_before_signing_in.pk}


def test_an_unavailable_product_stays_saved_but_cannot_be_bought(storefront):
    """An unavailable product may sit in the wishlist; it may not enter the cart (FR-037)."""
    from apps.catalog.models import Availability

    product = Product.objects.get(slug="zakey-core-c1")
    assert product.availability == Availability.UNAVAILABLE, "fixture is no longer unavailable"

    storefront.post(reverse("storefront:wishlist-toggle"), {"product": product.pk}, follow=True)

    page = storefront.get(reverse("storefront:wishlist"))
    assert page.context["wishlist_count"] == 1, "the unavailable product was dropped"
    assert product.name in page.content.decode()

    _add(storefront, product.variants.first(), 1)
    assert not CartLine.objects.exists(), "an unavailable product was purchasable"
