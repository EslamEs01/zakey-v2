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

    def test_a_review_carries_rating_title_body_author_product_and_creation_time(
        self, product, customer
    ):
        """FR-090: every field the requirement names survives the round trip."""
        review = services.submit_review(
            product=product,
            customer=customer,
            author_name="ندى إبراهيم",
            rating=4,
            title="قفل ممتاز",
            body="التركيب استغرق نصف ساعة والبصمة تعمل بدقة.",
        )
        review.refresh_from_db()

        assert 1 <= review.rating <= 5
        assert review.rating == 4
        assert review.title == "قفل ممتاز"
        assert review.body == "التركيب استغرق نصف ساعة والبصمة تعمل بدقة."
        assert review.author_name == "ندى إبراهيم"
        assert review.product_id == product.pk
        assert review.created_at is not None

    @pytest.mark.parametrize("rating", [0, 6, -1, 99])
    def test_rating_outside_one_to_five_is_refused(self, product, customer, rating):
        """FR-090: the rating a review carries is bounded to 1–5."""
        with pytest.raises(ValidationError):
            _submit(product, customer, rating=rating)
        assert not Review.objects.exists()

    def test_non_numeric_rating_is_refused(self, product, customer):
        with pytest.raises(ValidationError):
            _submit(product, customer, rating="خمسة")

    def test_database_rejects_an_out_of_range_rating_even_bypassing_the_service(
        self, product, customer
    ):
        """The bound is a check constraint, not just a service rule (FR-090)."""
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

    def test_the_database_refuses_a_second_review_of_one_product_by_one_customer(
        self, product, customer
    ):
        """FR-093: the one-per-product rule is a database constraint.

        The service refuses it first, so this writes straight to the table. The
        rule has to survive an import, a shell session, or a second code path
        that forgets to ask.
        """
        Review.objects.create(
            product=product,
            customer=customer,
            author_name="ندى",
            rating=5,
            body="قفل ممتاز وسهل التركيب.",
        )
        with pytest.raises(IntegrityError), transaction.atomic():
            Review.objects.create(
                product=product,
                customer=customer,
                author_name="ندى",
                rating=1,
                body="رأي ثانٍ من نفس العميل.",
            )

    def test_submission_is_rate_limited_per_customer(self, category, customer):
        """FR-095: review submission is rate-limited.

        Spam is posted across *different* products, so the one-per-product rule
        above does nothing against it; the ceiling that does is per customer per
        window.
        """
        from django.utils import timezone

        from apps.catalog.models import Product
        from apps.core import ratelimit
        from apps.core.models import PublicationStatus

        limit, _ = ratelimit.LIMITS["review"]
        targets = [
            Product.objects.create(
                slug=f"zakey-spam-target-{index}",
                name=f"قفل تجريبي {index}",
                category=category,
                status=PublicationStatus.PUBLISHED,
                published_at=timezone.now(),
            )
            for index in range(limit + 1)
        ]

        for target in targets[:limit]:
            _submit(target, customer)

        with pytest.raises(services.ReviewNotAllowed) as raised:
            _submit(targets[limit], customer)

        assert raised.value.messages == ["لقد أرسلت مراجعات كثيرة مؤخرًا؛ حاول لاحقًا."]
        assert Review.objects.count() == limit, "the throttled review was still stored"

    def test_html_in_a_review_is_stored_verbatim_and_escaped_on_render(
        self, storefront, customer
    ):
        """Storage keeps what was typed; the template escapes it (FR-095).

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
        """FR-092: a delivered order containing the product sets the flag."""
        _delivered_order(customer, variant)
        assert _submit(product, customer).is_verified_purchase is True

    @pytest.mark.parametrize(
        "status", [OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.SHIPPED]
    )
    def test_an_undelivered_order_does_not_verify(self, product, customer, variant, status):
        """FR-092: *delivered*, not merely placed — goods still in transit prove nothing."""
        order = _delivered_order(customer, variant)
        Order.objects.filter(pk=order.pk).update(status=status)
        assert _submit(product, customer).is_verified_purchase is False

    def test_another_customers_order_does_not_verify(
        self, product, customer, other_customer, variant
    ):
        """FR-092: the delivered order has to be the review author's own."""
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
        """FR-094: the system maintains both aggregates from the approved set."""
        services.approve(_submit(product, customer, rating=5))
        services.approve(_submit(product, other_customer, rating=3))

        product.refresh_from_db()
        assert product.review_count == 2
        assert product.rating_average == Decimal("4.00")

    def test_rejecting_removes_it_from_the_average(self, product, customer, other_customer):
        """FR-094: the aggregates track moderation in both directions."""
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
        """FR-094: never hand-edited.

        A hand-typed average would misreport what customers actually said, so
        the admin exposes both fields read-only.
        """
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
    def test_a_review_is_public_only_while_it_is_approved(self, storefront, customer):
        """FR-091: the three moderation states, and only one of them is public.

        Walks one review through `pending` → `approved` → `rejected` and asks
        the real product page each time, so "only approved reviews are public"
        is asserted against what a visitor can actually read.
        """
        from django.urls import reverse

        from apps.catalog.models import Product

        assert set(ReviewStatus.values) == {"pending", "approved", "rejected"}

        seeded = Product.objects.get(slug="zakey-apex-pro")
        url = reverse("storefront:product", kwargs={"slug": seeded.slug})
        body = "مراجعة تمر بالحالات الثلاث كلها."
        review = _submit(seeded, customer, body=body)

        assert review.status == ReviewStatus.PENDING
        assert body not in storefront.get(url).content.decode()

        services.approve(review)
        assert review.status == ReviewStatus.APPROVED
        assert body in storefront.get(url).content.decode()

        services.reject(review)
        assert review.status == ReviewStatus.REJECTED
        assert body not in storefront.get(url).content.decode()

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
