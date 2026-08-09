"""Review eligibility, moderation and aggregates (T-1202 – T-1204)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.orders.models import Order, OrderLine, OrderStatus
from apps.reviews import services
from apps.reviews.models import Review, ReviewStatus

pytestmark = pytest.mark.django_db


def _submit(product, customer=None, rating=5, body="قفل ممتاز وسهل التركيب."):
    return services.submit_review(
        product=product,
        customer=customer,
        author_name="ندى",
        rating=rating,
        body=body,
    )


def _delivered_order(customer, variant, number="ZK-DELIVERED"):
    order = Order.objects.create(
        number=number,
        customer=customer,
        email="nada@example.com",
        phone="01012345678",
        idempotency_key=f"idem-{number}",
        subtotal=Decimal("100.00"),
        grand_total=Decimal("114.00"),
        status=OrderStatus.DELIVERED,
    )
    OrderLine.objects.create(
        order=order,
        variant=variant,
        product_name=variant.product.name,
        product_slug=variant.product.slug,
        variant_label=variant.finish_label,
        sku=variant.sku,
        unit_price=variant.price,
        quantity=1,
        line_total=variant.price,
    )
    return order


# ---------------------------------------------------------------------------
# T-1204 — submission and validation
# ---------------------------------------------------------------------------


class TestSubmission:
    def test_new_reviews_are_pending_not_public(self, product, customer):
        review = _submit(product, customer)
        assert review.status == ReviewStatus.PENDING
        assert not Review.objects.approved().filter(pk=review.pk).exists()

    @pytest.mark.parametrize("rating", [0, 6, -1, 99])
    def test_rating_outside_one_to_five_is_refused(self, product, customer, rating):
        with pytest.raises(ValidationError):
            _submit(product, customer, rating=rating)
        assert not Review.objects.exists()

    def test_non_numeric_rating_is_refused(self, product, customer):
        with pytest.raises(ValidationError):
            _submit(product, customer, rating="خمسة")

    def test_database_rejects_an_out_of_range_rating_even_bypassing_the_service(
        self, product, customer
    ):
        """The bound is a check constraint, not just a service rule."""
        with pytest.raises(IntegrityError), transaction.atomic():
            Review.objects.create(
                product=product, customer=customer, author_name="x", rating=9, body="y"
            )

    def test_too_short_a_body_is_refused(self, product, customer):
        with pytest.raises(ValidationError):
            _submit(product, customer, body="جيد")

    def test_one_review_per_customer_per_product(self, product, customer):
        _submit(product, customer)
        with pytest.raises(services.ReviewNotAllowed):
            _submit(product, customer)
        assert Review.objects.count() == 1

    def test_html_in_a_review_is_stored_verbatim_and_escaped_on_render(
        self, storefront, customer
    ):
        """Storage keeps what was typed; the template escapes it.

        Uses the *seeded* catalogue rather than the unit `product` fixture: both
        claim the slug `zakey-apex-pro`, and creating one on top of the other
        collides on the unique constraint.
        """
        from django.urls import reverse

        from apps.catalog.models import Product

        seeded = Product.objects.get(slug="zakey-apex-pro")
        services.approve(
            _submit(seeded, customer, body="<script>alert('xss')</script> رائع جدا")
        )

        body = storefront.get(
            reverse("storefront:product", kwargs={"slug": seeded.slug})
        ).content.decode()
        assert "<script>alert(" not in body
        assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# T-1202 — verified purchase is derived
# ---------------------------------------------------------------------------


class TestVerifiedPurchase:
    def test_a_customer_without_orders_is_not_verified(self, product, customer):
        assert _submit(product, customer).is_verified_purchase is False

    def test_a_delivered_order_makes_the_review_verified(self, product, customer, variant):
        _delivered_order(customer, variant)
        assert _submit(product, customer).is_verified_purchase is True

    @pytest.mark.parametrize(
        "status", [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED]
    )
    def test_an_undelivered_order_does_not_verify(self, product, customer, variant, status):
        order = _delivered_order(customer, variant)
        Order.objects.filter(pk=order.pk).update(status=status)
        assert _submit(product, customer).is_verified_purchase is False

    def test_another_customers_order_does_not_verify(
        self, product, customer, other_customer, variant
    ):
        _delivered_order(other_customer, variant, number="ZK-THEIRS")
        assert _submit(product, customer).is_verified_purchase is False

    def test_a_submitter_cannot_claim_verification(self, product, customer):
        """The flag is not an input, so there is no field to lie in."""
        import inspect

        signature = inspect.signature(services.submit_review)
        assert "is_verified_purchase" not in signature.parameters


# ---------------------------------------------------------------------------
# T-1203 — system-maintained aggregates
# ---------------------------------------------------------------------------


class TestAggregates:
    def test_pending_reviews_do_not_count(self, product, customer):
        _submit(product, customer)
        product.refresh_from_db()
        assert product.review_count == 0
        assert product.rating_average == Decimal("0.00")

    def test_approving_updates_the_average_and_count(self, product, customer, other_customer):
        services.approve(_submit(product, customer, rating=5))
        services.approve(_submit(product, other_customer, rating=3))

        product.refresh_from_db()
        assert product.review_count == 2
        assert product.rating_average == Decimal("4.00")

    def test_rejecting_removes_it_from_the_average(self, product, customer, other_customer):
        first = _submit(product, customer, rating=5)
        second = _submit(product, other_customer, rating=1)
        services.approve(first)
        services.approve(second)

        services.reject(second)

        product.refresh_from_db()
        assert product.review_count == 1
        assert product.rating_average == Decimal("5.00")

    def test_aggregates_return_to_zero_when_all_reviews_are_rejected(self, product, customer):
        review = _submit(product, customer, rating=4)
        services.approve(review)
        services.reject(review)

        product.refresh_from_db()
        assert product.review_count == 0
        assert product.rating_average == Decimal("0.00")

    def test_recompute_is_idempotent(self, product, customer):
        services.approve(_submit(product, customer, rating=4))
        first = services.recompute_aggregate(product)
        second = services.recompute_aggregate(product)
        assert first == second

    def test_aggregate_fields_are_read_only_in_the_admin(self):
        """A hand-typed average would misreport what customers actually said."""
        from django.contrib import admin

        from apps.catalog.models import Product

        product_admin = admin.site._registry.get(Product)
        if product_admin is None:
            pytest.skip("Product is not registered in the admin")
        readonly = set(product_admin.readonly_fields or ())
        assert {"rating_average", "review_count"} <= readonly


# ---------------------------------------------------------------------------
# Moderation and visibility
# ---------------------------------------------------------------------------


class TestModeration:
    def test_only_approved_reviews_reach_the_storefront(self, storefront, customer):
        from django.urls import reverse

        from apps.catalog.models import Product

        seeded = Product.objects.get(slug="zakey-apex-pro")
        url = reverse("storefront:product", kwargs={"slug": seeded.slug})

        pending = _submit(seeded, customer, body="مراجعة قيد المراجعة تمامًا.")
        assert pending.body not in storefront.get(url).content.decode()

        services.approve(pending)
        assert pending.body in storefront.get(url).content.decode()

    def test_moderation_records_who_and_when(self, product, customer, user):
        review = services.approve(_submit(product, customer), actor=user)
        assert review.moderated_by == user
        assert review.moderated_at is not None

    def test_moderation_is_audited(self, product, customer, user):
        from apps.audit.models import AuditLog

        services.approve(_submit(product, customer), actor=user)
        assert AuditLog.objects.filter(object_repr__isnull=False).exists()
