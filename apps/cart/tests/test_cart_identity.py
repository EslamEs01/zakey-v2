"""Cart line identity (FR-030).

The approved storefront has a real defect this feature exists to correct::

    // static/src/js/state/store.js:24-26   add    -> keyed by (product, finish)
    // static/src/js/state/store.js:34      update -> keyed by product ONLY
    // static/src/js/state/store.js:41      remove -> keyed by product ONLY

so a customer with two finishes of the same lock in their basket could not
update or remove one without hitting the other. Here the key is
``(cart, variant)`` everywhere, enforced by the database.
"""

from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction

from apps.cart.models import Cart, CartLine

pytestmark = pytest.mark.django_db


@pytest.fixture
def cart(db, customer):
    return Cart.objects.create(customer=customer)


class TestTwoFinishesOfOneProduct:
    """The exact scenario the prototype got wrong."""

    def test_both_finishes_coexist_as_separate_lines(
        self, cart, variant, second_variant, stock, second_stock
    ):
        CartLine.objects.create(cart=cart, variant=variant, quantity=1)
        CartLine.objects.create(cart=cart, variant=second_variant, quantity=2)

        assert cart.lines.count() == 2
        assert variant.product_id == second_variant.product_id  # same product

    def test_updating_one_finish_leaves_the_other_untouched(
        self, cart, variant, second_variant, stock, second_stock
    ):
        first = CartLine.objects.create(cart=cart, variant=variant, quantity=1)
        second = CartLine.objects.create(cart=cart, variant=second_variant, quantity=2)

        first.quantity = 5
        first.save()

        second.refresh_from_db()
        assert second.quantity == 2, "updating one finish must not touch the other"

    def test_removing_one_finish_leaves_the_other_untouched(
        self, cart, variant, second_variant, stock, second_stock
    ):
        CartLine.objects.create(cart=cart, variant=variant, quantity=1)
        CartLine.objects.create(cart=cart, variant=second_variant, quantity=2)

        cart.lines.filter(variant=variant).delete()

        remaining = list(cart.lines.all())
        assert len(remaining) == 1
        assert remaining[0].variant_id == second_variant.pk


class TestUniqueIdentityIsEnforcedByTheDatabase:
    def test_same_variant_cannot_be_added_twice(self, cart, variant, stock):
        CartLine.objects.create(cart=cart, variant=variant, quantity=1)
        with pytest.raises(IntegrityError), transaction.atomic():
            CartLine.objects.create(cart=cart, variant=variant, quantity=1)

    def test_same_variant_in_two_carts_is_fine(self, customer, other_customer, variant, stock):
        cart_a = Cart.objects.create(customer=customer)
        cart_b = Cart.objects.create(customer=other_customer)
        CartLine.objects.create(cart=cart_a, variant=variant, quantity=1)
        CartLine.objects.create(cart=cart_b, variant=variant, quantity=1)
        assert CartLine.objects.count() == 2


class TestQuantityBounds:
    """1..9, matching the storefront bound at store.js:27-28 (FR-033)."""

    def test_quantity_above_nine_rejected(self, cart, variant, stock):
        with pytest.raises(IntegrityError), transaction.atomic():
            CartLine.objects.create(cart=cart, variant=variant, quantity=10)

    def test_quantity_zero_rejected(self, cart, variant, stock):
        with pytest.raises(IntegrityError), transaction.atomic():
            CartLine.objects.create(cart=cart, variant=variant, quantity=0)

    def test_nine_is_allowed(self, cart, variant, stock):
        line = CartLine.objects.create(cart=cart, variant=variant, quantity=9)
        assert line.quantity == 9


class TestOneActiveCartPerOwner:
    def test_customer_cannot_hold_two_active_carts(self, customer):
        Cart.objects.create(customer=customer)
        with pytest.raises(IntegrityError), transaction.atomic():
            Cart.objects.create(customer=customer)

    def test_session_cannot_hold_two_active_carts(self, db):
        Cart.objects.create(session_key="abc123")
        with pytest.raises(IntegrityError), transaction.atomic():
            Cart.objects.create(session_key="abc123")

    def test_a_converted_cart_frees_the_slot(self, customer):
        from apps.cart.models import CartStatus

        first = Cart.objects.create(customer=customer)
        first.status = CartStatus.CONVERTED
        first.save()
        Cart.objects.create(customer=customer)  # must not raise
        assert Cart.objects.filter(customer=customer).count() == 2

    def test_cart_line_protects_its_variant_from_deletion(self, cart, variant, stock):
        from django.db.models import ProtectedError

        CartLine.objects.create(cart=cart, variant=variant, quantity=1)
        with pytest.raises(ProtectedError):
            variant.delete()
