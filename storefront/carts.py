"""Request-scoped cart and wishlist resolution (T-1604, T-1606, FR-031, FR-037).

The prototype kept the basket in ``localStorage``, which made the browser the
database: quantities, prices and totals were whatever the client said they were.
Here the basket is a row, owned by either a signed-in customer or the visitor's
session, and every number the page shows is recomputed from it server-side
(FR-034).

Ownership is decided here and only here, so no view can accidentally widen it.
"""

from __future__ import annotations

from typing import Any

from apps.cart import services as cart_services
from apps.cart.models import Cart, CartStatus, Wishlist


def _session_key(request, *, create: bool) -> str:
    """The visitor's session key, creating a session only when we must.

    A brand-new visitor has no session key until something is stored, and
    ``Cart.session_key`` is the anonymous owner column — so a cart cannot be
    created without one. Read-only paths pass ``create=False`` and simply get an
    empty basket, which keeps a plain page view from setting a cookie.
    """
    if request.session.session_key is None:
        if not create:
            return ""
        request.session.create()
    return request.session.session_key or ""


def _owner(request, *, create: bool) -> dict[str, Any]:
    """Owner kwargs for the cart/wishlist services: customer, else session."""
    profile = None
    if request.user.is_authenticated:
        profile = getattr(request.user, "customer_profile", None)
    if profile is not None:
        return {"customer": profile}
    return {"session_key": _session_key(request, create=create)}


def get_cart(request, *, create: bool = False) -> Cart | None:
    """The active cart for this request, or ``None`` when there isn't one."""
    owner = _owner(request, create=create)
    if not owner.get("customer") and not owner.get("session_key"):
        return None
    if create:
        return cart_services.get_or_create_cart(**owner)
    return Cart.objects.filter(status=CartStatus.ACTIVE, **owner).first()


def get_wishlist(request, *, create: bool = False) -> Wishlist | None:
    owner = _owner(request, create=create)
    if not owner.get("customer") and not owner.get("session_key"):
        return None
    if create:
        return cart_services.get_or_create_wishlist(**owner)
    return Wishlist.objects.filter(**owner).first()


# ---------------------------------------------------------------------------
# Presentation
# ---------------------------------------------------------------------------


def line_records(totals) -> list[dict[str, Any]]:
    """Priced cart lines flattened for the template.

    Each record carries the ``variant_id`` the mutation forms post back. That
    is the canonical line identity (``UniqueConstraint(cart, variant)``), so two
    finishes of one product update and remove independently — the defect the
    prototype had at ``store.js:34,41``.
    """
    records = []
    for priced in totals.lines:
        variant = priced.variant
        product = variant.product
        image = product.primary_image
        records.append(
            {
                "variant_id": variant.pk,
                "sku": variant.sku,
                "product": product,
                "slug": product.slug,
                "name": product.name,
                "category": product.category.name if product.category_id else "",
                "finish_label": variant.finish_label,
                "image_path": image.src if image else "",
                "image_alt": image.alt if image else product.name,
                "unit_price": priced.unit_price,
                "quantity": priced.quantity,
                "total": priced.total,
                "available": priced.available,
                "reason": priced.reason,
            }
        )
    return records


def cart_context(request, *, cart=None, coupon_error: str = "") -> dict[str, Any]:
    """Everything the cart page and the header badge render.

    Totals come from :func:`apps.cart.services.price_cart`, which recomputes
    subtotal, discount, VAT and grand total from database rows on every request.
    Nothing here is read back from the client.
    """
    cart = cart if cart is not None else get_cart(request)
    if cart is None:
        return {
            "cart": None,
            "cart_lines": [],
            "cart_totals": None,
            "cart_count": 0,
            "coupon_error": coupon_error,
        }

    totals = cart_services.price_cart(cart, coupon=cart.coupon)
    records = line_records(totals)
    return {
        "cart": cart,
        "cart_lines": records,
        "cart_totals": totals,
        "cart_count": sum(record["quantity"] for record in records),
        "coupon_error": coupon_error,
    }


def wishlist_context(request, *, wishlist=None) -> dict[str, Any]:
    wishlist = wishlist if wishlist is not None else get_wishlist(request)
    if wishlist is None:
        return {"wishlist": None, "wishlist_products": [], "wishlist_count": 0}

    from apps.catalog import selectors

    items = wishlist.items.select_related("product__category").prefetch_related(
        "product__images", "product__variants__stock_item", "product__features"
    )
    products = [selectors._catalogue_product(item.product) for item in items]
    return {
        "wishlist": wishlist,
        "wishlist_products": products,
        "wishlist_count": len(products),
    }


def badge_counts(request) -> dict[str, Any]:
    """Header badge counts, plus which products are already on the wishlist.

    Aggregates rather than a full repricing: the header only needs "how many",
    and running ``price_cart`` on every page to render a number would cost the
    whole line/stock/coupon walk for nothing.

    ``wishlist_product_ids`` is what lets every product card render its heart in
    the correct pressed state on the server. Without it the card would have to
    start "off" and be corrected by a script after paint, which is both a flash
    of wrong state and a lie to assistive technology while it lasts.

    Reads only — a visitor who has never touched either gets zeroes and no
    session cookie.
    """
    from django.db.models import Sum

    cart = get_cart(request)
    wishlist = get_wishlist(request)
    quantity = (
        cart.lines.aggregate(total=Sum("quantity"))["total"] if cart is not None else 0
    )
    product_ids = (
        set(wishlist.items.values_list("product_id", flat=True))
        if wishlist is not None
        else set()
    )
    return {
        "cart_count": quantity or 0,
        "wishlist_count": len(product_ids),
        "wishlist_product_ids": product_ids,
    }


def merge_on_login(request, previous_session_key: str) -> None:
    """Fold the visitor's anonymous basket into their account on sign-in.

    Must be called with the session key captured *before* login, because Django
    cycles the key to prevent session fixation — after login the anonymous rows
    are no longer reachable by key.
    """
    profile = getattr(request.user, "customer_profile", None)
    if profile is None or not previous_session_key:
        return

    anonymous_cart = Cart.objects.filter(
        status=CartStatus.ACTIVE, session_key=previous_session_key, customer__isnull=True
    ).first()
    if anonymous_cart is not None:
        target = cart_services.get_or_create_cart(customer=profile)
        cart_services.merge_carts(anonymous_cart, target)

    anonymous_wishlist = Wishlist.objects.filter(
        session_key=previous_session_key, customer__isnull=True
    ).first()
    if anonymous_wishlist is not None:
        target_wishlist = cart_services.get_or_create_wishlist(customer=profile)
        cart_services.merge_wishlists(anonymous_wishlist, target_wishlist)
