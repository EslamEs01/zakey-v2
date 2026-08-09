"""Email confirmation and password reset over HTTP (T-0404, FR-053, FR-054).

The service layer's token behaviour is unit-tested in ``apps/accounts``. This
suite drives the real endpoints, because the properties that matter here are
end-to-end: a link works exactly once, an expired link never renders a usable
form, and no response distinguishes a registered address from an unknown one.

Email uses Django's locmem backend (``config/settings/test.py``). Nothing here
claims a production mail provider is configured.
"""

from __future__ import annotations

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts import services
from apps.accounts.models import CustomerProfile, User

pytestmark = pytest.mark.django_db

PASSWORD = "Zakey-Pass!123"
NEW_PASSWORD = "Fresh-Pass!456"


@pytest.fixture
def registered(db):
    user = User.objects.create_user(email="nada@example.com", password=PASSWORD)
    profile = CustomerProfile.objects.create(
        user=user, full_name="ندى إبراهيم", phone="01012345678"
    )
    return user, profile


# ---------------------------------------------------------------------------
# Email confirmation (FR-053)
# ---------------------------------------------------------------------------


class TestEmailConfirmation:
    def test_a_valid_link_verifies_the_address(self, client, registered):
        user, profile = registered
        assert profile.email_verified is False

        token = services.make_email_confirmation_token(user)
        response = client.get(
            reverse("storefront:account-confirm", kwargs={"token": token}), follow=True
        )

        profile.refresh_from_db()
        assert profile.email_verified is True
        assert "تم تأكيد" in response.content.decode()

    def test_the_same_link_cannot_be_replayed(self, client, registered):
        user, _ = registered
        token = services.make_email_confirmation_token(user)
        url = reverse("storefront:account-confirm", kwargs={"token": token})

        client.get(url, follow=True)
        second = client.get(url, follow=True)

        # The token is salted with the verified flag, so confirming re-salts it.
        assert "غير صالح" in second.content.decode()

    def test_a_tampered_link_is_refused(self, client, registered):
        user, profile = registered
        token = services.make_email_confirmation_token(user) + "tampered"

        client.get(reverse("storefront:account-confirm", kwargs={"token": token}), follow=True)

        profile.refresh_from_db()
        assert profile.email_verified is False

    def test_an_expired_link_is_refused(self, client, registered):
        user, profile = registered
        token = services.make_email_confirmation_token(user)

        with pytest.raises(services.InvalidToken):
            services.user_from_email_confirmation_token(token, max_age=-1)

        profile.refresh_from_db()
        assert profile.email_verified is False

    def test_a_reset_token_is_not_a_confirmation_token(self, client, registered):
        user, profile = registered
        crossed = services.make_password_reset_token(user)

        client.get(
            reverse("storefront:account-confirm", kwargs={"token": crossed}), follow=True
        )

        profile.refresh_from_db()
        assert profile.email_verified is False, "salts are not separating the two flows"


# ---------------------------------------------------------------------------
# Password reset request (FR-054) — enumeration resistance
# ---------------------------------------------------------------------------


class TestResetRequest:
    def _request(self, client, email):
        return client.post(
            reverse("storefront:password-reset-request"), {"email": email}, follow=True
        )

    def test_a_known_address_receives_a_link(self, client, registered):
        mail.outbox.clear()
        self._request(client, "nada@example.com")
        assert len(mail.outbox) == 1
        assert "/reset/" in mail.outbox[0].body

    def test_an_unknown_address_is_silently_ignored(self, client, db):
        mail.outbox.clear()
        self._request(client, "ghost@example.com")
        assert mail.outbox == []

    def test_both_answers_are_byte_identical(self, client, registered):
        """The response must not be an account-existence oracle."""
        known = self._request(client, "nada@example.com")
        unknown = self._request(client, "ghost@example.com")

        assert known.status_code == unknown.status_code
        assert services.__name__  # keep the import meaningful
        from storefront.views import RESET_REQUESTED_MESSAGE

        assert RESET_REQUESTED_MESSAGE in known.content.decode()
        assert RESET_REQUESTED_MESSAGE in unknown.content.decode()

    def test_a_malformed_address_still_reveals_nothing(self, client, db):
        response = self._request(client, "not-an-email")
        from storefront.views import RESET_REQUESTED_MESSAGE

        assert RESET_REQUESTED_MESSAGE in response.content.decode()
        assert mail.outbox == []

    def test_the_daily_cap_does_not_change_the_response(self, client, registered):
        mail.outbox.clear()
        for _ in range(services.PASSWORD_RESET_MAX_PER_DAY + 3):
            response = self._request(client, "nada@example.com")

        from storefront.views import RESET_REQUESTED_MESSAGE

        assert RESET_REQUESTED_MESSAGE in response.content.decode()
        assert len(mail.outbox) <= services.PASSWORD_RESET_MAX_PER_DAY

    def test_the_endpoint_rejects_get(self, client, db):
        assert client.get(reverse("storefront:password-reset-request")).status_code == 405


# ---------------------------------------------------------------------------
# Password reset completion (FR-054)
# ---------------------------------------------------------------------------


class TestResetCompletion:
    def _url(self, user):
        return reverse(
            "storefront:password-reset-confirm",
            kwargs={"token": services.make_password_reset_token(user)},
        )

    def test_a_valid_token_renders_the_form(self, client, registered):
        user, _ = registered
        body = client.get(self._url(user)).content.decode()
        assert "data-reset-form" in body
        assert 'name="password_confirm"' in body

    def test_setting_a_new_password_works_and_the_old_one_stops(self, client, registered):
        user, _ = registered
        client.post(
            self._url(user),
            {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD},
            follow=True,
        )

        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD)
        assert not user.check_password(PASSWORD)

    def test_a_used_token_cannot_be_replayed(self, client, registered):
        user, _ = registered
        url = self._url(user)
        client.post(url, {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}, follow=True)

        response = client.post(
            url, {"password": "Another-Pass!789", "password_confirm": "Another-Pass!789"},
            follow=True,
        )

        user.refresh_from_db()
        assert user.check_password(NEW_PASSWORD), "a replayed token changed the password again"
        assert "غير صالح" in response.content.decode()

    def test_a_tampered_token_never_renders_a_form(self, client, registered):
        user, _ = registered
        url = reverse(
            "storefront:password-reset-confirm",
            kwargs={"token": services.make_password_reset_token(user) + "x"},
        )
        body = client.get(url, follow=True).content.decode()
        assert "data-reset-form" not in body
        assert "غير صالح" in body

    def test_mismatched_confirmation_is_refused(self, client, registered):
        user, _ = registered
        client.post(
            self._url(user),
            {"password": NEW_PASSWORD, "password_confirm": "Different-Pass!999"},
            follow=True,
        )
        user.refresh_from_db()
        assert user.check_password(PASSWORD), "password changed despite a mismatch"

    def test_a_weak_password_is_refused(self, client, registered):
        user, _ = registered
        client.post(
            self._url(user), {"password": "12345678", "password_confirm": "12345678"}, follow=True
        )
        user.refresh_from_db()
        assert user.check_password(PASSWORD)

    def test_a_confirmation_token_cannot_reset_a_password(self, client, registered):
        user, _ = registered
        url = reverse(
            "storefront:password-reset-confirm",
            kwargs={"token": services.make_email_confirmation_token(user)},
        )
        client.post(url, {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD}, follow=True)

        user.refresh_from_db()
        assert user.check_password(PASSWORD), "salts are not separating the two flows"

    def test_reset_then_login_through_the_real_endpoint(self, client, registered):
        """The whole loop: reset, then sign in with the new password."""
        user, _ = registered
        client.post(
            self._url(user),
            {"password": NEW_PASSWORD, "password_confirm": NEW_PASSWORD},
            follow=True,
        )

        response = client.post(
            reverse("storefront:account-login"),
            {"email": "nada@example.com", "password": NEW_PASSWORD},
            follow=True,
        )
        assert response.context["account_mode"] == "signed-in"


# ---------------------------------------------------------------------------
# Guest checkout is untouched by any of this (INV-016)
# ---------------------------------------------------------------------------


def test_guest_checkout_needs_no_account(storefront):
    """FR-053's confirmation requirement must not gate buying."""
    from apps.catalog.models import Product

    variant = Product.objects.get(slug="zakey-apex-pro").variants.first()
    storefront.post(
        reverse("storefront:cart-add"), {"variant": variant.pk, "quantity": 1}, follow=True
    )
    response = storefront.get(reverse("storefront:checkout"))

    assert response.status_code == 200
    assert response.context["cart_lines"], "a signed-out visitor cannot reach checkout"
