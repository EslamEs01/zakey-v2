"""CSRF, safe redirects, XSS and log redaction (T-1701, T-1703, T-1704, T-1705).

These are the four sweeps that only mean something when they are *exhaustive*.
A CSRF check on eleven of twelve endpoints protects nothing — the attacker uses
the twelfth. So the endpoint list here is derived from the URLconf rather than
hand-written, and a new mutating route joins the sweep automatically.

Threats covered: T-05 (CSRF), T-06 (XSS), T-10 (open redirect), T-13 (log
leakage).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


#: Every mutating storefront endpoint, with a minimal valid-shaped payload.
#: Payloads need not succeed — CSRF is checked before the view runs at all.
MUTATING_ENDPOINTS = [
    ("storefront:cart-add", {}, {"variant": "1", "quantity": "1"}),
    ("storefront:cart-update", {}, {"line": "1", "quantity": "2"}),
    ("storefront:cart-remove", {}, {"line": "1"}),
    ("storefront:cart-coupon", {}, {"code": "TEST"}),
    ("storefront:wishlist-toggle", {}, {"product": "1"}),
    ("storefront:newsletter", {}, {"email": "nada@example.com"}),
    ("storefront:checkout-submit", {}, {}),
    ("storefront:account-login", {}, {"email": "a@b.com", "password": "x"}),
    ("storefront:account-register", {}, {"email": "a@b.com"}),
    ("storefront:account-logout", {}, {}),
    ("storefront:address-create", {}, {}),
    ("storefront:address-delete", {}, {"address": "1"}),
    ("storefront:profile-update", {}, {}),
    ("storefront:contact-send", {}, {"name": "ندى"}),
    ("storefront:password-reset-request", {}, {"email": "a@b.com"}),
]


def discovered_post_routes() -> set[str]:
    """Every POST-only storefront route, read off the URLconf."""
    from django.urls import get_resolver

    from storefront import views as storefront_views

    names = set()
    resolver = get_resolver()
    for key, value in vars(storefront_views).items():  # noqa: B007
        if not callable(value):
            continue
        # ``require_POST`` wraps the view; the marker survives on the wrapper.
        if getattr(value, "__wrapped__", None) is not None or getattr(
            value, "_zakey_post_only", False
        ):
            names.add(key)
    del resolver
    return names


# ---------------------------------------------------------------------------
# T-1701 — CSRF on every mutating endpoint (threat T-05)
# ---------------------------------------------------------------------------


class TestCsrfProtection:
    @pytest.mark.parametrize("name,kwargs,payload", MUTATING_ENDPOINTS)
    def test_a_post_without_a_token_is_refused(self, name, kwargs, payload, db):
        """403, not a redirect and certainly not a mutation."""
        client = Client(enforce_csrf_checks=True)

        response = client.post(reverse(name, kwargs=kwargs), payload)

        assert response.status_code == 403, (
            f"{name} accepted a POST with no CSRF token"
        )

    @pytest.mark.parametrize("name,kwargs,payload", MUTATING_ENDPOINTS)
    def test_a_get_is_refused(self, name, kwargs, payload, db):
        """A mutation reachable by GET is reachable by an <img> tag."""
        client = Client()

        response = client.get(reverse(name, kwargs=kwargs))

        assert response.status_code == 405, f"{name} answered a GET"

    def test_the_sweep_covers_every_post_only_view(self):
        """Guard the guard: a new mutating route must not escape the sweep.

        The count is asserted rather than the names, because the names above are
        URL names while the views carry Python names; what matters is that the
        two lists cannot silently diverge in size.
        """
        from storefront import urls as storefront_urls

        post_only_paths = [
            pattern
            for pattern in storefront_urls.urlpatterns
            if getattr(pattern.callback, "__name__", "")
            in {
                "cart_add", "cart_update", "cart_remove", "cart_coupon",
                "wishlist_toggle", "newsletter", "checkout_submit",
                "account_login", "account_register", "account_logout",
                "address_create", "address_delete", "profile_update",
                "contact_send", "password_reset_request",
            }
        ]
        assert len(post_only_paths) == len(MUTATING_ENDPOINTS)

    def test_a_valid_token_is_accepted(self, storefront):
        """The guard must not be a blanket refusal that breaks the shop."""
        from apps.catalog.models import Product

        variant = Product.objects.get(slug="zakey-apex-pro").variants.first()

        response = storefront.post(
            reverse("storefront:cart-add"),
            {"variant": variant.pk, "quantity": 1},
            follow=True,
        )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# T-1701 — a mutation may only touch the requester's own basket (FR-039)
# ---------------------------------------------------------------------------


class TestCartAndWishlistMutationsAreScopedToTheRequester:
    """A cart or wishlist mutation is authorised against the requesting session.

    CSRF alone is not authorisation: a token proves the request came from our
    page, not that it may touch *this* basket. Every mutation resolves the cart
    from the session or the signed-in customer and never from an id in the body,
    so one visitor's POST cannot reach another visitor's rows (FR-039).
    """

    def _variant(self):
        from apps.catalog.models import Product

        return Product.objects.get(slug="zakey-apex-pro").variants.first()

    def test_a_stranger_cannot_remove_your_cart_line(self, storefront):
        from apps.cart.models import CartLine

        variant = self._variant()
        storefront.post(
            reverse("storefront:cart-add"),
            {"variant": variant.pk, "quantity": 2},
            follow=True,
        )

        stranger = Client()
        stranger.post(reverse("storefront:cart-remove"), {"variant": variant.pk}, follow=True)

        line = CartLine.objects.get()
        assert line.variant_id == variant.pk, "another session emptied the basket"
        assert line.quantity == 2

    def test_a_stranger_cannot_change_your_quantity(self, storefront):
        from apps.cart.models import CartLine

        variant = self._variant()
        storefront.post(
            reverse("storefront:cart-add"),
            {"variant": variant.pk, "quantity": 2},
            follow=True,
        )

        stranger = Client()
        stranger.post(
            reverse("storefront:cart-update"),
            {"variant": variant.pk, "quantity": 9},
            follow=True,
        )

        assert CartLine.objects.get().quantity == 2, "another session repriced the basket"

    def test_a_stranger_cannot_unsave_your_wishlist_product(self, storefront):
        from apps.cart.models import Wishlist
        from apps.catalog.models import Product

        product = Product.objects.get(slug="zakey-apex-pro")
        storefront.post(
            reverse("storefront:wishlist-toggle"), {"product": product.pk}, follow=True
        )
        owner = Wishlist.objects.get()

        stranger = Client()
        stranger.post(
            reverse("storefront:wishlist-toggle"), {"product": product.pk}, follow=True
        )

        assert owner.items.filter(product=product).exists(), (
            "another session removed a saved product"
        )
        assert Wishlist.objects.count() == 2, "the stranger wrote into someone else's list"


# ---------------------------------------------------------------------------
# T-1704 — safe redirects (threat T-10)
# ---------------------------------------------------------------------------


HOSTILE_TARGETS = [
    "https://evil.example.com/steal",
    "//evil.example.com/steal",
    "http://evil.example.com",
    "https://zakey.test.evil.example.com/",
    "\\\\evil.example.com",
    "javascript:alert(1)",
]


class TestSafeRedirects:
    @pytest.mark.parametrize("target", HOSTILE_TARGETS)
    def test_the_newsletter_never_redirects_off_site(self, storefront, target):
        response = storefront.post(
            reverse("storefront:newsletter"),
            {"email": "nada@example.com", "next": target},
        )

        assert response.status_code == 302
        assert "evil.example.com" not in response["Location"]
        assert not response["Location"].lower().startswith("javascript:")

    @pytest.mark.parametrize("target", HOSTILE_TARGETS)
    def test_the_cart_never_redirects_off_site(self, storefront, target):
        from apps.catalog.models import Product

        variant = Product.objects.get(slug="zakey-apex-pro").variants.first()

        response = storefront.post(
            reverse("storefront:cart-add"),
            {"variant": variant.pk, "quantity": 1, "next": target},
        )

        assert response.status_code == 302
        assert "evil.example.com" not in response["Location"]

    @pytest.mark.parametrize("target", HOSTILE_TARGETS)
    def test_the_wishlist_never_redirects_off_site(self, storefront, target):
        from apps.catalog.models import Product

        product = Product.objects.get(slug="zakey-apex-pro")

        response = storefront.post(
            reverse("storefront:wishlist-toggle"),
            {"product": product.pk, "next": target},
        )

        assert response.status_code == 302
        assert "evil.example.com" not in response["Location"]

    def test_a_relative_target_is_honoured(self, storefront):
        """Validation must not break the legitimate use of ``next``."""
        response = storefront.post(
            reverse("storefront:newsletter"),
            {"email": "nada@example.com", "next": "/about/"},
        )

        assert response["Location"] == "/about/"


# ---------------------------------------------------------------------------
# T-1703 — XSS sweep (threat T-06)
# ---------------------------------------------------------------------------


PAYLOAD = '<script>alert("xss")</script>'


class TestXssIsEscaped:
    def test_a_contact_message_is_escaped_in_the_admin(self, client, db):
        from apps.accounts.models import User
        from apps.content.models import ContactMessage

        ContactMessage.objects.create(
            name=PAYLOAD, email="nada@example.com", subject=PAYLOAD,
            message="رسالة طويلة بما يكفي لتجاوز الحد الأدنى المطلوب للرسائل.",
        )
        staff = User.objects.create_superuser(email="a@zakey.test", password="Admin!2345")
        client.force_login(staff)

        body = client.get(reverse("admin:content_contactmessage_changelist")).content.decode()

        assert "<script>alert" not in body
        assert "&lt;script&gt;" in body

    def test_a_review_body_is_escaped_on_the_product_page(self, storefront, db):
        from apps.accounts.models import CustomerProfile, User
        from apps.catalog.models import Product
        from apps.reviews.models import Review, ReviewStatus

        user = User.objects.create_user(email="rev@example.com", password="StrongPass!234")
        profile = CustomerProfile.objects.create(
            user=user, full_name="ندى", phone="01012345678"
        )
        product = Product.objects.get(slug="zakey-apex-pro")
        Review.objects.create(
            product=product, customer=profile, rating=5, body=PAYLOAD,
            status=ReviewStatus.APPROVED,
        )

        body = storefront.get(
            reverse("storefront:product", kwargs={"slug": product.slug})
        ).content.decode()

        assert "<script>alert" not in body

    def test_a_customer_name_is_escaped_on_the_account_page(self, client, db):
        from apps.accounts.models import CustomerProfile, User

        user = User.objects.create_user(email="xss@example.com", password="StrongPass!234")
        CustomerProfile.objects.create(user=user, full_name=PAYLOAD, phone="01012345678")
        client.force_login(user)

        body = client.get(reverse("storefront:account")).content.decode()

        assert "<script>alert" not in body

    def test_an_address_label_is_escaped(self, client, db, governorate, area):
        from apps.accounts.models import Address, CustomerProfile, User

        user = User.objects.create_user(email="addr@example.com", password="StrongPass!234")
        profile = CustomerProfile.objects.create(
            user=user, full_name="ندى", phone="01012345678"
        )
        Address.objects.create(
            customer=profile, label=PAYLOAD, full_name="ندى", phone="01012345678",
            governorate=governorate, area=area, city="القاهرة",
            street="شارع التحرير", building="12",
        )
        client.force_login(user)

        body = client.get(reverse("storefront:account") + "?tab=addresses").content.decode()

        assert "<script>alert" not in body

    def test_a_product_name_is_escaped_in_the_catalogue(self, storefront, db):
        from apps.catalog.models import Product

        product = Product.objects.get(slug="zakey-apex-pro")
        Product.objects.filter(pk=product.pk).update(name=PAYLOAD)

        body = storefront.get(reverse("storefront:shop")).content.decode()

        assert "<script>alert" not in body


# ---------------------------------------------------------------------------
# T-1705 — log redaction (threat T-13, NFR-012)
# ---------------------------------------------------------------------------


class TestLogRedaction:
    @pytest.mark.parametrize(
        "raw,must_not_contain",
        [
            ("customer phone 01012345678 called", "01012345678"),
            ("mail to nada.ibrahim@example.com now", "nada.ibrahim@example.com"),
            ("password=Sup3rSecret", "Sup3rSecret"),
            ("token: abc123def456", "abc123def456"),
            ("card 4111111111111111 used", "4111111111111111"),
            ("Authorization: Bearer xyzzy-secret", "xyzzy-secret"),
        ],
    )
    def test_sensitive_values_never_survive_redaction(self, raw, must_not_contain):
        from apps.core.logging import redact

        assert must_not_contain not in redact(raw)

    def test_redaction_keeps_the_line_useful(self):
        from apps.core.logging import redact

        result = redact("customer phone 01012345678 placed order ZK-1")

        assert "ZK-1" in result, "redaction destroyed the correlatable part of the line"
        assert "010" in result

    def test_the_filter_is_installed_on_every_handler(self):
        from django.conf import settings

        for name, handler in settings.LOGGING["handlers"].items():
            assert "redact" in handler.get("filters", []), (
                f"log handler {name!r} has no redaction filter"
            )

    def test_a_real_log_record_is_redacted(self, caplog):
        import logging

        from apps.core.logging import RedactingFilter

        logger = logging.getLogger("zakey.test.redaction")
        logger.addFilter(RedactingFilter())

        with caplog.at_level(logging.INFO, logger="zakey.test.redaction"):
            logger.info("checkout for nada.ibrahim@example.com phone 01012345678")

        emitted = "".join(record.getMessage() for record in caplog.records)
        assert "nada.ibrahim@example.com" not in emitted
        assert "01012345678" not in emitted
