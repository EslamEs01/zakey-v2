"""Registration / email-confirm / login / logout / password-reset (T-0404).

Locks the framework-level auth surface against FR-050 – FR-058 and the exact
Arabic copy in frontend-contract.md §4. Views land in Phase 16; everything
below exercises only forms and services.
"""

from __future__ import annotations

from unittest.mock import patch  # noqa: F401 — kept for symmetry with future view tests

import pytest
from django.contrib.auth import get_user_model, password_validation  # noqa: F401
from django.core import signing
from django.db import IntegrityError, transaction
from django.utils import timezone  # noqa: F401

from apps.accounts import forms, services
from apps.accounts.models import CustomerProfile

User = get_user_model()

pytestmark = pytest.mark.django_db

GOOD = {
    "email": "New@Example.COM",
    "full_name": "ندى إبراهيم",
    "mobile": "01012345678",
    "password": "Zakey-Pass!123",
    "password_confirm": "Zakey-Pass!123",
}


def _form(**overrides):
    return forms.RegistrationForm(data={**GOOD, **overrides})


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_register_creates_user_profile_and_confirmation_token():
    form = _form()
    assert form.is_valid(), form.errors.as_json()

    result = services.register(form)

    assert result.user.email == "new@example.com"  # normalised (FR-050)
    assert result.user.is_active is True
    assert result.requires_email_confirmation is True
    profile = result.profile
    assert profile.full_name == "ندى إبراهيم"
    assert profile.phone == "01012345678"
    assert profile.email_verified is False
    assert result.user.check_password(GOOD["password"])
    assert result.user.is_staff is False and result.user.is_superuser is False
    assert result.confirmation_token


def test_confirm_email_marks_profile_verified_and_token_dies(  # round-trip
):
    form = _form()
    assert form.is_valid(), form.errors.as_json()
    result = services.register(form)

    user = services.confirm_email(result.confirmation_token)

    assert user.customer_profile.email_verified is True
    # single-use: the state salt moved, so the same bytes never verify again
    with pytest.raises(services.InvalidToken):
        services.confirm_email(result.confirmation_token)


# ---------------------------------------------------------------------------
# Email / name / mobile validation with the exact storefront copy (T-0404)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("email", ["", "plain-address", "a@b", "a b@c.com"])
def test_bad_email_rejected_with_exact_message(email):
    form = _form(email=email)
    form.is_valid()
    assert forms.INVALID_EMAIL_MESSAGE in form.errors.as_text()


def test_mobile_invalid_message_exact_and_normalisation():
    form = _form(mobile="+٢٠ ١٠١ ٢٣٤ ٥٦٧٨")
    assert form.is_valid(), form.errors.as_json()
    assert form.cleaned_data["mobile"] == "01012345678"

    bad = _form(mobile="01312345678")
    assert not bad.is_valid()
    assert "اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا." in bad.errors.as_text()


@pytest.mark.parametrize("name", ["Ahmed Ali", "ن", "☺︎☺︎"])
def test_full_name_requires_arabic_and_min_length(name):
    form = _form(full_name=name)
    assert not form.is_valid()
    assert "اكتب الاسم بالكامل بالعربية." in form.errors.as_text()


# ---------------------------------------------------------------------------
# Duplicate rejection without an account-enumeration Oracle (FR-052)
# ---------------------------------------------------------------------------


def test_duplicate_email_is_rejected():
    """FR-052: a second registration cannot claim an email already in use."""
    first = _form()
    assert first.is_valid(), first.errors.as_json()
    services.register(first)

    second = _form(email="new@example.com", mobile="01112345678")  # same email, casefold
    assert not second.is_valid()
    assert "email" in second.errors

    # Message must never concede the account exists (FR-052 wording guard).
    for message in second.errors["email"]:
        assert "موجود" not in message and "account" not in message.lower()


def test_duplicate_verified_mobile_is_rejected(customer):
    """FR-052: a mobile already verified on another profile cannot be reused."""
    # `customer`, not `user`: the rule guards a mobile already VERIFIED on a
    # profile, and the bare `user` fixture deliberately has no profile row.
    profile = customer
    profile.phone_verified = True
    profile.save(update_fields=["phone_verified", "updated_at"])

    form = _form(email="fresh@example.com", mobile="01012345678")
    assert not form.is_valid()
    assert "mobile" in form.errors


def test_email_uniqueness_is_enforced_by_the_database(user):
    """FR-052: the email rule is a column constraint, not only form logic.

    Form validation is bypassable — an import, a shell session, a data migration
    — so the guarantee has to still hold one layer down.
    """
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            User.objects.create_user(email=user.email, password="Another-Pass!123")


def test_phone_uniqueness_binds_verified_customers_only(customer, other_customer):
    """FR-052: the phone rule is *partial*, and both halves are asserted here.

    Unverified duplicates are a data-entry reality and stay legal — two people
    can mistype the same number. The moment a second profile claims that number
    as *verified*, the database refuses, which is what makes a verified mobile
    usable as an identity at all.
    """
    other_customer.phone = customer.phone
    other_customer.save(update_fields=["phone", "updated_at"])
    assert CustomerProfile.objects.filter(phone=customer.phone).count() == 2

    customer.phone_verified = True
    customer.save(update_fields=["phone_verified", "updated_at"])

    other_customer.phone_verified = True
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            other_customer.save(update_fields=["phone_verified", "updated_at"])


# ---------------------------------------------------------------------------
# Password policy + confirm/reset token round-trip (FR-054)
# ---------------------------------------------------------------------------


def test_password_too_short_is_rejected():
    form = _form(password="Short!9", password_confirm="Short!9")
    assert not form.is_valid()
    assert "password" in form.errors


def test_password_confirm_mismatch_is_rejected():
    form = _form(password_confirm="Zakey-Pass!124")
    assert not form.is_valid()
    assert "كلمتا المرور غير متطابقتين." in form.errors.as_text()


def test_password_similar_to_email_is_rejected():
    form = _form(password="new@example.com1", password_confirm="new@example.com1")
    assert not form.is_valid()
    assert "password" in form.errors


def test_password_reset_token_round_trip_single_use(user):
    token = services.make_password_reset_token(user)

    def new_form():
        # Refetch so the token's password-hash state is always evaluated
        # against the freshest row (TokenStore is stateless).
        fresh_user = User.objects.get(pk=user.pk)
        return forms.SetNewPasswordForm(
            data={"password": "Fresh-Pass!456", "password_confirm": "Fresh-Pass!456"},
            user=fresh_user,
        )

    changed_form = new_form()
    assert changed_form.is_valid(), changed_form.errors.as_json()
    updated = services.reset_password(token, changed_form)
    assert User.objects.get(pk=user.pk).check_password("Fresh-Pass!456")
    assert updated.check_password("Fresh-Pass!456")

    # single-use: changing the password re-salted the token (FR-054)
    with pytest.raises(services.InvalidToken):
        services.reset_password(token, new_form())
    with pytest.raises(services.InvalidToken):
        services.user_from_password_reset_token(token + "tampered")


def test_confirmation_token_is_not_a_reset_token_and_reverse(user):
    confirm = services.make_email_confirmation_token(user)
    reset = services.make_password_reset_token(user)
    with pytest.raises(services.InvalidToken):
        services.user_from_password_reset_token(confirm)
    with pytest.raises(services.InvalidToken):
        services.user_from_email_confirmation_token(reset)


def test_password_reset_request_never_reveals_existence(user):
    existing = forms.PasswordResetRequestForm(data={"email": user.email})
    ghost = forms.PasswordResetRequestForm(data={"email": "nobody@zakey.test"})
    assert existing.is_valid()
    assert ghost.is_valid()  # identical outward behaviour (FR-054)


def test_reset_requests_are_capped_per_email(user):
    from django.core import mail

    for _ in range(services.PASSWORD_RESET_MAX_PER_DAY):
        services.request_password_reset(user.email)
    assert len(mail.outbox) == services.PASSWORD_RESET_MAX_PER_DAY

    services.request_password_reset(user.email)  # sixth request is swallowed
    assert len(mail.outbox) == services.PASSWORD_RESET_MAX_PER_DAY


def test_forged_reset_token_is_rejected():
    from django.core import signing

    forged = signing.TimestampSigner(salt=services.PASSWORD_RESET_SALT).sign_object(
        {"uid": 999_999, "state": "whatever"}
    )
    with pytest.raises(services.InvalidToken):
        services.user_from_password_reset_token(forged)


# ---------------------------------------------------------------------------
# Login / logout round-trips (services level; views land in Phase 16)
# ---------------------------------------------------------------------------


def test_login_success_returns_user(user):
    ok, returned = services.login(user.email, "StrongPass!234", "127.0.0.1")
    assert ok is True
    assert returned.pk == user.pk


def test_login_failure_is_masked(user):
    ok1, _u1 = services.login(user.email, "wrong-password", "127.0.0.1")
    ok2, _u2 = services.login("nobody@zakey.test", "wrong-password", "127.0.0.1")
    assert (ok1, _u1) == (False, None) == (ok2, _u2)


# ---------------------------------------------------------------------------
# Guest checkout must never depend on auth (FR-053 accept criterion)
# ---------------------------------------------------------------------------


def test_guest_checkout_stays_possible(client):
    """The cart page is reachable unsigned (T-0404 accept), and a registration
    attempt does not touch the anonymous cart the guest was building."""
    cart_response = client.get("/cart/")
    assert cart_response.status_code == 200

    from apps.cart.models import Cart

    cart = Cart.objects.create(session_key="guest-session")
    form = _form(email="guest@example.com", mobile="01012345678")
    assert form.is_valid(), form.errors.as_json()
    result = services.register(form)

    cart.refresh_from_db()
    assert cart.customer_id is None  # registration never steals the guest cart
    assert result.user.email == "guest@example.com"


def test_registration_form_does_not_require_any_authentication():
    # Registration itself must work from an anonymous process boundary —
    # the form carries no request/user at all.
    form = _form(email="anon@example.com", mobile="01012345678")
    assert form.is_valid(), form.errors.as_json()
