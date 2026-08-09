"""Review submission, moderation and aggregates (T-1202 – T-1204, FR-090 – FR-095).

Three rules do most of the work here:

* **Eligibility is derived, never claimed.** ``is_verified_purchase`` is computed
  from delivered orders, so a customer cannot mark their own review verified.
* **Aggregates are maintained by the system.** ``Product.rating_average`` and
  ``review_count`` are recomputed from approved reviews on every moderation
  event. They are never writable by hand — a hand-edited average is a lie about
  what customers said.
* **Nothing is public until a human approves it.** New reviews are ``pending``;
  the storefront only ever reads ``approved``.
"""

from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone

from .models import Review, ReviewStatus


class ReviewNotAllowed(ValidationError):
    pass


def has_purchased(customer, product) -> bool:
    """True when this customer has a *delivered* order containing the product.

    Delivered, not merely placed: an order that was cancelled or is still in
    transit is not evidence that anyone used the thing.
    """
    if customer is None:
        return False
    from apps.orders.models import Order, OrderStatus

    return Order.objects.filter(
        customer=customer,
        status=OrderStatus.DELIVERED,
        lines__variant__product=product,
    ).exists()


@transaction.atomic
def submit_review(*, product, customer, author_name: str, rating: int, body: str, title: str = "") -> Review:
    """Create a pending review (FR-090, FR-093, FR-095).

    The rating bound is enforced here *and* by a database check constraint, so a
    value outside 1–5 cannot arrive by any route.
    """
    try:
        rating = int(rating)
    except (TypeError, ValueError):
        raise ValidationError("اختر تقييمًا من 1 إلى 5.") from None
    if not 1 <= rating <= 5:
        raise ValidationError("اختر تقييمًا من 1 إلى 5.")

    body = (body or "").strip()
    if len(body) < 10:
        raise ValidationError("اكتب 10 أحرف على الأقل في مراجعتك.")

    if customer is not None and Review.objects.filter(product=product, customer=customer).exists():
        # One review per customer per product (FR-093).
        raise ReviewNotAllowed("لقد قيّمت هذا المنتج من قبل.")

    # Review spam is posted in bulk across *different* products, so the
    # one-per-product rule above does nothing to stop it (T-1707, threat T-14).
    # The ceiling is per customer, checked only once the submission is otherwise
    # valid, so a rejected draft never burns an attempt.
    from apps.core import ratelimit

    identifier = str(getattr(customer, "pk", None) or (author_name or "anonymous"))
    if not ratelimit.allow("review", identifier):
        raise ReviewNotAllowed("لقد أرسلت مراجعات كثيرة مؤخرًا؛ حاول لاحقًا.")

    return Review.objects.create(
        product=product,
        customer=customer,
        author_name=(author_name or "").strip()[:120],
        rating=rating,
        title=title.strip()[:160],
        body=body,
        # Derived, never supplied by the submitter (FR-092).
        is_verified_purchase=has_purchased(customer, product),
        status=ReviewStatus.PENDING,
    )


@transaction.atomic
def approve(review: Review, *, actor=None) -> Review:
    """Publish a review and refresh the product's aggregate (FR-091, FR-094)."""
    review.status = ReviewStatus.APPROVED
    review.moderated_by = actor
    review.moderated_at = timezone.now()
    review.save(update_fields=["status", "moderated_by", "moderated_at", "updated_at"])
    recompute_aggregate(review.product)
    _audit(review, "approve", actor)
    return review


@transaction.atomic
def reject(review: Review, *, actor=None, note: str = "") -> Review:
    """Hide a review and refresh the aggregate.

    Rejecting must recompute too: a review that was approved and is now rejected
    has to stop counting towards the average, or the score keeps crediting
    content nobody can read.
    """
    review.status = ReviewStatus.REJECTED
    review.moderated_by = actor
    review.moderated_at = timezone.now()
    if note:
        review.staff_response = note[:1000]
    review.save(
        update_fields=[
            "status",
            "moderated_by",
            "moderated_at",
            "staff_response",
            "updated_at",
        ]
    )
    recompute_aggregate(review.product)
    _audit(review, "reject", actor)
    return review


def recompute_aggregate(product) -> tuple[Decimal, int]:
    """Recompute ``rating_average`` and ``review_count`` from approved reviews.

    Returns the new values. This is the only writer of those two fields; the
    admin exposes them read-only.
    """
    stats = Review.objects.filter(product=product, status=ReviewStatus.APPROVED).aggregate(
        average=models.Avg("rating"), total=models.Count("id")
    )
    total = stats["total"] or 0
    average = (
        Decimal(str(stats["average"])).quantize(Decimal("0.01"))
        if stats["average"] is not None
        else Decimal("0.00")
    )
    product.rating_average = average
    product.review_count = total
    product.save(update_fields=["rating_average", "review_count", "updated_at"])
    return average, total


def _audit(review: Review, action: str, actor) -> None:
    from apps.audit.models import AuditAction
    from apps.audit.services import record_audit

    record_audit(
        actor=actor,
        action=AuditAction.STATUS_CHANGE,
        obj=review,
        changes={"review_action": action, "status": review.status},
    )
