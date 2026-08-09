"""Rate limiting on public write endpoints (T-1707, threat T-14).

Login has its own progressive lockout, tested in ``test_login_rate_limit``.
This covers the other four: coupon, review, contact and newsletter.

The property that matters twice over is that **a limit is never an oracle**.
Refusing with "too many attempts" would confirm to a coupon-prober that their
earlier guesses were being evaluated, and would tell a spammer exactly when to
back off. So every refusal here is indistinguishable from the ordinary outcome.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.core import ratelimit

pytestmark = pytest.mark.django_db


class TestTheLimiterItself:
    def test_attempts_below_the_ceiling_are_allowed(self):
        limit, _ = ratelimit.LIMITS["contact"]

        assert all(ratelimit.allow("contact", "1.2.3.4") for _ in range(limit))

    def test_the_attempt_after_the_ceiling_is_refused(self):
        limit, _ = ratelimit.LIMITS["contact"]
        for _ in range(limit):
            ratelimit.allow("contact", "1.2.3.4")

        assert ratelimit.allow("contact", "1.2.3.4") is False

    def test_limits_are_scoped_per_identifier(self):
        limit, _ = ratelimit.LIMITS["contact"]
        for _ in range(limit + 2):
            ratelimit.allow("contact", "1.2.3.4")

        assert ratelimit.allow("contact", "5.6.7.8") is True

    def test_limits_are_scoped_per_endpoint(self):
        limit, _ = ratelimit.LIMITS["coupon"]
        for _ in range(limit + 2):
            ratelimit.allow("coupon", "1.2.3.4")

        assert ratelimit.allow("contact", "1.2.3.4") is True

    def test_the_cache_key_never_contains_the_raw_identifier(self):
        """Personal data must not be written into the cache backend (NFR-012)."""
        key = ratelimit._key("contact", "nada.ibrahim@example.com")

        assert "nada.ibrahim@example.com" not in key
        assert "nada" not in key

    def test_every_scope_has_a_ceiling_and_a_window(self):
        for scope, (limit, window) in ratelimit.LIMITS.items():
            assert limit > 0, f"{scope} has no ceiling"
            assert window > 0, f"{scope} has no window"

    def test_reset_clears_the_window(self):
        limit, _ = ratelimit.LIMITS["contact"]
        for _ in range(limit + 2):
            ratelimit.allow("contact", "1.2.3.4")

        ratelimit.reset("contact", "1.2.3.4")

        assert ratelimit.allow("contact", "1.2.3.4") is True


class TestCouponProbing:
    def test_repeated_coupon_attempts_are_throttled(self, storefront):
        limit, _ = ratelimit.LIMITS["coupon"]
        url = reverse("storefront:cart-coupon")

        for _ in range(limit + 3):
            response = storefront.post(url, {"coupon": "GUESS"}, follow=True)

        assert response.status_code == 200

    def test_the_refusal_is_indistinguishable_from_an_invalid_code(self, storefront):
        """A distinct 'too many attempts' would confirm the guesses were read."""
        from apps.promotions import services as promotions_services

        limit, _ = ratelimit.LIMITS["coupon"]
        url = reverse("storefront:cart-coupon")

        first = storefront.post(url, {"coupon": "NOPE"}, follow=True).content.decode()
        for _ in range(limit + 3):
            throttled = storefront.post(
                url, {"coupon": "NOPE"}, follow=True
            ).content.decode()

        assert promotions_services.REJECTED_MESSAGE in first
        assert promotions_services.REJECTED_MESSAGE in throttled


class TestContactFlood:
    def test_messages_stop_being_stored_past_the_ceiling(self, storefront):
        from apps.content.models import ContactMessage

        limit, _ = ratelimit.LIMITS["contact"]
        url = reverse("storefront:contact-send")
        payload = {
            "name": "ندى",
            "email": "nada@example.com",
            "phone": "01012345678",
            "subject": "استفسار",
            "message": "رسالة طويلة بما يكفي لتجاوز الحد الأدنى المطلوب للرسائل.",
        }

        for _ in range(limit + 5):
            storefront.post(url, payload, follow=True)

        assert ContactMessage.objects.count() <= limit

    def test_a_throttled_send_is_indistinguishable_from_an_accepted_one(
        self, storefront
    ):
        """The limiter must not tell a spammer when it started dropping them.

        Asserted on the response itself rather than on a flash message: the
        contact page does not render messages, so a message assertion would
        pass or fail for reasons unrelated to the property under test.
        """
        limit, _ = ratelimit.LIMITS["contact"]
        url = reverse("storefront:contact-send")
        payload = {
            "name": "ندى",
            "email": "nada@example.com",
            "phone": "01012345678",
            "subject": "استفسار",
            "message": "رسالة طويلة بما يكفي لتجاوز الحد الأدنى المطلوب للرسائل.",
        }

        accepted = storefront.post(url, payload, follow=True)
        for _ in range(limit + 5):
            throttled = storefront.post(url, payload, follow=True)

        assert accepted.status_code == throttled.status_code == 200
        assert accepted.redirect_chain == throttled.redirect_chain
        body = throttled.content.decode()
        assert "كثيرة" not in body, "the refusal announced itself"
        assert "too many" not in body.lower()


class TestNewsletterFlood:
    def test_signups_stop_being_stored_past_the_ceiling(self, storefront):
        from apps.content.models import NewsletterSubscription

        limit, _ = ratelimit.LIMITS["newsletter"]
        url = reverse("storefront:newsletter")

        for index in range(limit + 5):
            storefront.post(url, {"email": f"person{index}@example.com"}, follow=True)

        assert NewsletterSubscription.objects.count() <= limit

    def test_a_throttled_signup_is_indistinguishable_from_an_accepted_one(
        self, storefront
    ):
        limit, _ = ratelimit.LIMITS["newsletter"]
        url = reverse("storefront:newsletter")

        accepted = storefront.post(
            url, {"email": "first@example.com"}, follow=True
        )
        for index in range(limit + 5):
            throttled = storefront.post(
                url, {"email": f"person{index}@example.com"}, follow=True
            )

        assert accepted.status_code == throttled.status_code == 200
        body = throttled.content.decode()
        assert "كثيرة" not in body, "the refusal announced itself"
        assert "too many" not in body.lower()


class TestReviewSpam:
    def test_a_customer_cannot_post_unlimited_reviews(self, db, customer, category):
        """The one-per-product rule does nothing against bulk across products."""
        from apps.catalog.models import Product
        from apps.reviews.services import ReviewNotAllowed, submit_review

        limit, _ = ratelimit.LIMITS["review"]
        products = [
            Product.objects.create(slug=f"p{index}", name=f"منتج {index}", category=category)
            for index in range(limit + 3)
        ]

        accepted = 0
        for product in products:
            try:
                submit_review(
                    product=product,
                    customer=customer,
                    author_name="ندى",
                    rating=5,
                    body="مراجعة طويلة بما يكفي.",
                )
                accepted += 1
            except ReviewNotAllowed:
                break

        assert accepted == limit

    def test_a_rejected_draft_does_not_burn_an_attempt(self, db, customer, product):
        """The ceiling counts submissions, not typos."""
        from django.core.exceptions import ValidationError

        from apps.reviews.services import submit_review

        for _ in range(3):
            with pytest.raises(ValidationError):
                submit_review(
                    product=product, customer=customer, author_name="ندى",
                    rating=5, body="قصيرة",  # too short
                )

        assert ratelimit.remaining("review", str(customer.pk)) == (
            ratelimit.LIMITS["review"][0]
        )
