"""Storefront authentication forms (T-0404, FR-050 – FR-058).

Framework-level only: these forms are rendered by the storefront views that
Phase 16 wires up. Until then nothing imports them from a URL-conf.

Field labels are the storefront's ``data-label`` values and error messages are
lifted verbatim from ``frontend-contract.md`` §4 — never reword them.
"""

from __future__ import annotations

import time

from django import forms
from django.contrib.auth import authenticate, get_user_model, password_validation
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .validators import (
    INVALID_MOBILE_MESSAGE,
    is_valid_egyptian_mobile,
    normalize_egyptian_mobile,
)

# Exact storefront messages (frontend-contract.md §4) — do not reword.
INVALID_EMAIL_MESSAGE = "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com."
INVALID_FULL_NAME_MESSAGE = "اكتب الاسم بالكامل بالعربية."

# Generic copy shared by every login failure path, on purpose: the response
# must not reveal whether the email exists or the account is locked (FR-058).
GENERIC_LOGIN_ERROR_MESSAGE = "بيانات الدخول غير صحيحة. حاول مرة أخرى."

_ARABIC_LETTER_RE = r"[\u0600-\u06FF]"

# Storefront email rule is the JS regex /^[^\s@]+@[^\s@]+\.[^\s@]+$/ —
# deliberately narrower than full RFC validation so server matches browser.
STOREFRONT_EMAIL_RE = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

#: The total duration a failed login always runs to, so existing-email
#: failures (password hash verify + rate-limit writes) take the same wall
#: time as unknown-email ones. Deliberately generous versus two Argon2 checks.
MINIMUM_LOGIN_RESPONSE_SECONDS = 0.5


class UnifiedEmailField(forms.RegexField):
    """One message for missing OR malformed email — the storefront's JS
    ``required("email")`` shows the format message for both cases."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 254)
        super().__init__(
            STOREFRONT_EMAIL_RE,
            label="البريد الإلكتروني",
            error_messages={
                "required": INVALID_EMAIL_MESSAGE,
                "invalid": INVALID_EMAIL_MESSAGE,
            },
            **kwargs,
        )

    def to_python(self, value):
        return super().to_python(value).strip().lower()


class MobileField(forms.CharField):
    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 16)
        super().__init__(
            label="رقم الموبايل",
            error_messages={
                "required": INVALID_MOBILE_MESSAGE,
                "invalid": INVALID_MOBILE_MESSAGE,
            },
            **kwargs,
        )

    def clean(self, value):
        value = super().clean(value)
        if not is_valid_egyptian_mobile(value):
            raise ValidationError(INVALID_MOBILE_MESSAGE, code="invalid")
        return normalize_egyptian_mobile(value)


class FullNameField(forms.CharField):
    """≥2 chars and contains an Arabic letter (checkout.js fullName rule)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("max_length", 120)
        super().__init__(
            label="الاسم بالكامل",
            error_messages={
                "required": INVALID_FULL_NAME_MESSAGE,
                "invalid": INVALID_FULL_NAME_MESSAGE,
            },
            **kwargs,
        )

    def clean(self, value):
        value = super().clean(value).strip()
        if len(value) < 2:
            raise ValidationError(INVALID_FULL_NAME_MESSAGE, code="invalid")
        RegexValidator(_ARABIC_LETTER_RE, message=INVALID_FULL_NAME_MESSAGE, code="invalid")(value)
        return value


class PasswordFormMixin:
    """Behaviour for a ``password`` / ``password_confirm`` pair checked
    against the configured Django password policy (min-length 10, common,
    numeric, similarity). Fields are declared on each concrete form because
    a plain mixin cannot inject fields into the declared-fields collector."""

    PASSWORD_FIELD_DECLARATIONS = {
        "password": forms.CharField(label="كلمة المرور", min_length=10, strip=False),
        "password_confirm": forms.CharField(label="تأكيد كلمة المرور", strip=False),
    }

    @property
    def user_for_password_validation(self):
        """User the similarity validator compares against; registration
        overrides this with the unsaved instance carrying email/name."""
        return None

    def clean_password(self):
        password = self.cleaned_data["password"]
        password_validation.validate_password(password, user=self.user_for_password_validation)
        return password

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password and confirm and password != confirm:
            raise ValidationError(
                {"password_confirm": "كلمتا المرور غير متطابقتين."}, code="password_mismatch"
            )
        return cleaned

    def set_user_password(self, user):
        user.set_password(self.cleaned_data["password"])
        return user


class RegistrationForm(PasswordFormMixin, forms.Form):
    """New customer account (FR-050, FR-053).

    No ModelForm anywhere near visited input: the form hard-ignores every key
    it does not declare, so ``is_staff``/``is_superuser``/``email_verified``
    can never be flipped through it (FR-057, T-0407).

    Duplicate identities are rejected — but with wording that cannot confirm
    an existing account; the registration service emails the real owner a
    sign-in hint instead of showing it here.
    """

    email = UnifiedEmailField()
    full_name = FullNameField()
    mobile = MobileField()
    password = PasswordFormMixin.PASSWORD_FIELD_DECLARATIONS["password"]
    password_confirm = PasswordFormMixin.PASSWORD_FIELD_DECLARATIONS["password_confirm"]
    accepts_marketing = forms.BooleanField(label="الاشتراك في العروض", required=False)

    field_order = ["email", "full_name", "mobile", "password", "password_confirm", "accepts_marketing"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].help_text = password_validation.password_validators_help_text_html()

    @property
    def user_for_password_validation(self):
        # The similarity validator reads real model attributes only; an
        # unsaved instance carrying email is enough.
        data = getattr(self, "cleaned_data", {}) or {}
        return get_user_model()(email=data.get("email", ""))

    def clean_email(self):
        email = self.cleaned_data["email"]
        # FR-052 uniqueness without an account-existence Oracle: the message
        # says the address "cannot be used", never "the account exists", and
        # services.send_duplicate_registration_notice() informs the real owner
        # out of band.
        if get_user_model().objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "لا يمكن استخدام هذا البريد الإلكتروني لإنشاء حساب جديد.", code="duplicate"
            )
        return email

    def clean_mobile(self):
        mobile = self.cleaned_data["mobile"]
        from .models import CustomerProfile

        if CustomerProfile.objects.filter(phone=mobile, phone_verified=True).exists():
            raise ValidationError(
                "لا يمكن استخدام رقم الموبايل هذا لإنشاء حساب جديد.", code="duplicate"
            )
        return mobile


class LoginForm(forms.Form):
    """Storefront sign-in (FR-058).

    Every failure — unknown email, wrong password, locked account, inactive
    account — returns the identical ``GENERIC_LOGIN_ERROR_MESSAGE`` after the
    identical minimum wall time, so neither copy nor timing reveals which part
    failed. Rate limiting runs in :func:`apps.accounts.services.login` for
    EVERY attempt, including unknown emails, so unknown-identifier hammering
    is throttled too.
    """

    email = UnifiedEmailField()
    password = forms.CharField(label="كلمة المرور", strip=False)

    error_messages = {"invalid_login": GENERIC_LOGIN_ERROR_MESSAGE}

    def __init__(self, *args, client_ip: str = "", **kwargs):
        self._client_ip = client_ip
        self._started_at = 0.0
        super().__init__(*args, **kwargs)

    def clean(self):
        from . import services

        self._started_at = time.monotonic()
        cleaned = super().clean()
        success, _ = services.login(
            cleaned.get("email") or "", cleaned.get("password") or "", self._client_ip
        )
        if not success:
            self._equalise_timing()
            raise ValidationError(self.error_messages["invalid_login"], code="invalid_login")
        return cleaned

    def get_user(self):
        """The authenticated user, guaranteed present after ``is_valid()``."""
        return authenticate(
            email=self.cleaned_data["email"], password=self.cleaned_data["password"]
        )

    def _equalise_timing(self):
        remaining = MINIMUM_LOGIN_RESPONSE_SECONDS - (time.monotonic() - self._started_at)
        if remaining > 0:
            time.sleep(remaining)


class PasswordResetRequestForm(forms.Form):
    """Requests a reset link without ever answering "does this email have an
    account?" (FR-054): unknown addresses validate; the service layer simply
    does not mail them."""

    email = UnifiedEmailField()


class SetNewPasswordForm(PasswordFormMixin, forms.Form):
    """Final step of the reset flow. ``user`` comes from a token the service
    layer already validated; the form should only ever be bound for a real,
    verified token bearer."""

    password = PasswordFormMixin.PASSWORD_FIELD_DECLARATIONS["password"]
    password_confirm = PasswordFormMixin.PASSWORD_FIELD_DECLARATIONS["password_confirm"]

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    @property
    def user_for_password_validation(self):
        return self.user

    def confirm_password_change(self):
        """Persist the new password; the caller owns the token invalidation."""
        if self.user is None or not self.is_valid():
            raise ValidationError("تعذر تغيير كلمة المرور.")
        user = self.set_user_password(self.user)
        user.save(update_fields=["password"])
        return user
