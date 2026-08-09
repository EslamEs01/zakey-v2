"""Owner-scoped object access (T-0406, FR-056, INV-010, SC-007).

One lookup helper, one contract: objects a customer owns are reachable ONLY
through that owner (or, for anonymous baskets/wishlists, the session key that
created them). Every miss — absent, unowned, unauthenticated — surfaces as a
uniform 404, so the response never distinguishes "this id exists but is not
yours" from "this id does not exist".

The mapping below only trusts the real schema; where a model has no direct
customer edge (``CartLine``), the chain walks to the owning object first.
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

OWNER_LOOKUPS: dict[str, str] = {
    # model label lower            -> ORM path from the model to CustomerProfile
    "cart.cart": "customer",
    "cart.cartline": "cart__customer",
    "cart.wishlist": "customer",
    "cart.wishlistitem": "wishlist__customer",
    "orders.order": "customer",
    "orders.orderaddress": "order__customer",
    "accounts.address": "customer",
    "accounts.customerprofile": "",  # the profile itself
}

# Session-scoped look-ups for the two models anonymous visitors can own. The
# session key is the credential here — an anonymous user carries only their
# own.
SESSION_LOOKUPS: dict[str, str] = {
    "cart.cart": "session_key",
    "cart.cartline": "cart__session_key",
    "cart.wishlist": "session_key",
    "cart.wishlistitem": "wishlist__session_key",
}


def get_owned_object(model, pk: Any, user, session_key: str = ""):
    """Fetch ``model[pk]`` as ``user`` (or the anonymous ``session_key``).

    Raises :class:`django.http.Http404` for cross-user, signed-out-when-owned
    (account objects) or session-mismatched (anonymous objects) access; raises
    :class:`django.core.exceptions.PermissionDenied` when a signed-in caller
    asks for an anonymous-owned object and we cannot honour the lookup.
    """
    label = model._meta.label_lower
    if label not in OWNER_LOOKUPS:  # hard fail: extending this map is explicit
        raise LookupError(f"{label} is not a registered customer-owned model")

    qs = model._default_manager.all()
    if user is not None and getattr(user, "is_authenticated", False):
        path = OWNER_LOOKUPS[label]
        if path:
            qs = qs.filter(**{f"{path}__user": user})
        else:
            qs = qs.filter(user=user)
    elif session_key and label in SESSION_LOOKUPS:
        qs = qs.filter(**{SESSION_LOOKUPS[label]: session_key})
    else:
        raise PermissionDenied("login-required")  # views turn this into a 302
    return get_object_or_404(qs, pk=pk)


class OwnerScopedObjectMixin:
    """Class-based-view glue around :func:`get_owned_object`.

    Views set ``model`` (or ``owned_model``) and optionally
    ``owner_url_kwarg``; the mixin hands them the owner-scoped object or lets
    the helper raise 404/PermissionDenied.
    """

    owner_url_kwarg = "pk"

    def get_owned_object(self):
        model = getattr(self, "owned_model", None) or getattr(self, "model", None)
        if model is None:  # pragma: no cover - configuration error
            raise ImproperlyConfigured("OwnerScopedObjectMixin needs a model")
        key = self.request.session.session_key or ""
        return get_owned_object(
            model, self.kwargs[self.owner_url_kwarg], self.request.user, key
        )

    def get_object(self, queryset=None):  # noqa: ARG002 - ownership beats the qs
        return self.get_owned_object()


# Imported late, for the class-based mixin only.
from django.core.exceptions import ImproperlyConfigured  # noqa: E402
