"""Authentication and account services (T-0404 / T-0405, FR-050 – FR-058).

Everything here is request-agnostic: views, future carts/checkout code and
management commands all call the same functions. No HTTP, no messages
framework, no templates.

Covers:

* registration with mandatory email confirmation (FR-053) while guest
  checkout stays untouched (INV-016),
* single-use, time-limited, salted signed tokens for email confirmation and
  password reset (FR-054),
* login rate limiting keyed by identifier AND IP with progressive lockout
  (FR-058), with reset tokens optionally throttled the same way,
* enumeration-resistant reporting throughout.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from django.contrib.auth import authenticate
from django.core import signing
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import CustomerProfile, User

# ---------------------------------------------------------------------------
# Tunables (FR-058). Seconds; the progressive ladder doubles the lock.
# ---------------------------------------------------------------------------

#: Free failures before any lock engages.
FREE_ATTEMPTS = 3

#: Lock for ``BASE_LOCK_SECONDS * 2 ** (failure_streak - FREE_ATTEMPTS - 1)``
#: at the end of each failing streak; capped by ``MAX_LOCK_SECONDS``.
BASE_LOCK_SECONDS = 30
MAX_LOCK_SECONDS = 3600

#: How long a failure streak counts as one streak (no successes in between).
ATTEMPT_WINDOW_SECONDS = 3600

#: Cap on reset-link requests per email per day (FR-054, prevent mail bombs).
PASSWORD_RESET_MAX_PER_DAY = 5


# ---------------------------------------------------------------------------
# Registration + confirmation tokens (T-0404, FR-053 / FR-054)
# ---------------------------------------------------------------------------

# Token payloads are salted with account state that changes on exactly the
# event the token guards, so a token is single-use by construction:
#
# * confirmation tokens expire once the email is verified,
# * reset tokens expire once the password changes.
#
# ``TimestampSigner`` (``unsign_object(..., max_age=...)``) enforces the time
# limit at the framework level.

EMAIL_CONFIRMATION_SALT = "accounts.email-confirmation.v1"
EMAIL_CONFIRMATION_MAX_AGE = 60 * 60 * 24  # 24 hours

PASSWORD_RESET_SALT = "accounts.password-reset.v1"
PASSWORD_RESET_MAX_AGE = 60 * 60  # 1 hour


class InvalidToken(Exception):
    """Any token failure: malformed, expired, unknown user, or stale salt."""


def _email_state(user: User) -> str:
    """Secret-adjacent state baked into the token payload, so old tokens die
    exactly on the events they guard:

    * confirmation tokens die once the email is verified;
    * reset tokens die once the password changes.

    ``OneToOneField`` reverse accessors raise ``RelatedObjectDoesNotExist``,
    so the profile side is probed defensively.
    """
    try:
        profile = user.customer_profile
    except CustomerProfile.DoesNotExist:
        profile = None
    verified = getattr(profile, "email_verified", False) if profile else False
    return f"{int(bool(verified))}:{user.password}"


def make_email_confirmation_token(user: User) -> str:
    return signing.TimestampSigner(salt=EMAIL_CONFIRMATION_SALT).sign_object(
        {"uid": user.pk, "state": _email_state(user)}
    )


def user_from_email_confirmation_token(token: str, max_age: int = EMAIL_CONFIRMATION_MAX_AGE) -> User:
    return _user_from_token(token, EMAIL_CONFIRMATION_SALT, max_age)


def make_password_reset_token(user: User) -> str:
    return signing.TimestampSigner(salt=PASSWORD_RESET_SALT).sign_object(
        {"uid": user.pk, "state": _email_state(user)}
    )


def user_from_password_reset_token(token: str, max_age: int = PASSWORD_RESET_MAX_AGE) -> User:
    return _user_from_token(token, PASSWORD_RESET_SALT, max_age)


def _user_from_token(token: str, salt: str, max_age: int) -> User:
    try:
        payload = signing.TimestampSigner(salt=salt).unsign_object(token, max_age=max_age)
        user = User.objects.get(pk=payload["uid"])
    except (signing.BadSignature, ValueError, TypeError, KeyError, User.DoesNotExist) as exc:
        raise InvalidToken("الرابط غير صالح أو انتهت صلاحيته.") from exc
    if payload.get("state") != _email_state(user):
        raise InvalidToken("الرابط غير صالح أو انتهت صلاحيته.")
    return user


@dataclass
class RegistrationResult:
    user: User
    profile: CustomerProfile
    confirmation_token: str
    requires_email_confirmation: bool


@transaction.atomic
def register(form) -> RegistrationResult:
    """Create an inactive-until-confirmed customer (FR-053).

    The account can sign in immediately but the storefront gates verified-only
    features on ``CustomerProfile.email_verified``; guests never need any of
    this to check out.
    """
    user = User.objects.create_user(email=form.cleaned_data["email"], password=None)
    form.set_user_password(user)
    user.save(update_fields=["password"])
    profile = CustomerProfile.objects.create(
        user=user,
        full_name=form.cleaned_data["full_name"],
        phone=form.cleaned_data["mobile"],
        accepts_marketing=form.cleaned_data.get("accepts_marketing", False),
    )
    return RegistrationResult(
        user=user,
        profile=profile,
        confirmation_token=make_email_confirmation_token(user),
        requires_email_confirmation=True,
    )


def send_duplicate_registration_notice(email: str) -> None:
    """Out-of-band heads-up to the real owner when a duplicate registration is
    attempted; the visible form message stays generic on purpose."""
    from django.core.mail import send_mail

    send_mail(
        subject="محاولة إنشاء حساب جديد ببريدك",
        message=(
            "حاول شخص ما إنشاء حساب جديد باستخدام هذا البريد الإلكتروني. "
            "إن لم تكن أنت، تجاهل هذه الرسالة بأمان."
        ),
        from_email=None,
        recipient_list=[email],
        fail_silently=True,
    )


def confirm_email(token: str) -> User:
    """Consume a confirmation token. Returns the now-verified user."""
    user = user_from_email_confirmation_token(token)
    try:
        profile = user.customer_profile
    except CustomerProfile.DoesNotExist:  # pragma: no cover - defensive only
        profile = CustomerProfile.objects.create(user=user, full_name=user.email)
    profile.email_verified = True
    profile.save(update_fields=["email_verified", "updated_at"])
    return user


def request_password_reset(email: str) -> None:
    """Send a single-use reset link if — and only if — the email exists.

    Callers never learn the difference; the per-email daily cap keeps this
    from being a mail-bomb amplifier (FR-054).
    """
    from django.core.mail import send_mail

    user = User.objects.filter(email__iexact=email).first()
    if user is None:
        return
    # Throttle on the EMAIL, not the account id: an attacker who knows an
    # address cannot turn this into a mailbox flood by re-registering.
    if not _reset_rate_allows(email.strip().lower()):
        return
    token = make_password_reset_token(user)
    send_mail(
        subject="إعادة تعيين كلمة المرور",
        message=f"لإعادة تعيين كلمة المرور استخدم هذا الرابط خلال ساعة: /reset/{token}",
        from_email=None,
        recipient_list=[user.email],
        fail_silently=True,
    )


def _reset_rate_allows(identifier: str) -> bool:
    key = f"auth:reset-count:{identifier}:{timezone.now().date().isoformat()}"
    try:
        added = cache.add(key, 1, timeout=86400)
        count = 1 if added else cache.incr(key)
    except ValueError:  # pragma: no cover - defensive against racy backends
        cache.set(key, 1, timeout=86400)
        count = 1
    return count <= PASSWORD_RESET_MAX_PER_DAY


def reset_password(token: str, form) -> User:
    """Consume a reset token and set the new password in one transaction
    (FR-054 single-use: changing the password re-salts the token).

    The returned user is re-read after the write. ``form.user`` is a *different*
    Python object from the one the token resolved to, so returning the token's
    instance would hand the caller a stale password hash — and callers do use
    it (``django.contrib.auth.login`` re-derives the session hash from it,
    which would immediately invalidate the new session).
    """
    user = user_from_password_reset_token(token)
    with transaction.atomic():
        form.confirm_password_change()  # persists the password
    return User.objects.get(pk=user.pk)


# ---------------------------------------------------------------------------
# Login rate limiting (T-0405, FR-058)
# ---------------------------------------------------------------------------


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _keys(identifier: str, ip: str) -> tuple[str, str]:
    """Cache keys for the dual scope: per-account and per-IP."""
    return (
        f"auth:login:id:{_sha(identifier.strip().lower())}",
        f"auth:login:ip:{_sha(ip.strip().lower())}",
    )


def _get_count(key: str) -> int:
    try:
        return int(cache.get(key, 0))
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return 0


def _failures_until_locked(key: str) -> int:
    """Free attempts remaining on this key.

    ``_count`` keeps *excess* failures: attempt ``FREE_ATTEMPTS+1`` is the first
    one stored (value 1) and engages the lock. So while fewer than
    ``FREE_ATTEMPTS`` failures happened the callers see ``FREE_ATTEMPTS``,
    ``FREE_ATTEMPTS-1``, ... free attempts left, and zero once the key is locked.
    """
    count = _get_count(key)
    if count <= 0:
        # No excess failure recorded yet. The streak may still hold
        # ``FREE_ATTEMPTS`` failures but none excess, so all are still free.
        # How many real failures happened is tracked implicitly by the streak,
        # which we keep alongside the excess counter.
        streak = _get_count(f"{key}:streak")
        return max(FREE_ATTEMPTS - streak, 0)
    locked_until = cache.get(f"{key}:locked-until")
    if locked_until is not None:
        return 0
    return 0


def is_locked_out(identifier: str, ip: str) -> bool:
    """True when EITHER the account key or the IP key holds an active lock."""
    now = int(time.time())
    for key in _keys(identifier, ip):
        locked_until = cache.get(f"{key}:locked-until")
        if isinstance(locked_until, int) and locked_until > now:
            return True
    return False


def remaining_free_attempts(identifier: str, ip: str) -> int:
    return min(_failures_until_locked(key) for key in _keys(identifier, ip))


def record_failed_login(identifier: str, ip: str) -> None:
    now = int(time.time())
    for key in _keys(identifier, ip):
        # Streak: raw count of consecutive failures in the attempt window.
        try:
            added = cache.add(f"{key}:streak", 1, timeout=ATTEMPT_WINDOW_SECONDS)
            streak = 1 if added else cache.incr(f"{key}:streak")
        except ValueError:  # pragma: no cover - key evicted mid-flight
            cache.set(f"{key}:streak", 1, timeout=ATTEMPT_WINDOW_SECONDS)
            streak = 1
        if streak > FREE_ATTEMPTS:
            # Excess failure: this one engages (or re-engages) a longer lock.
            try:
                added = cache.add(key, 1, timeout=ATTEMPT_WINDOW_SECONDS)
                excess = 1 if added else cache.incr(key)
            except ValueError:  # pragma: no cover
                cache.set(key, 1, timeout=ATTEMPT_WINDOW_SECONDS)
                excess = 1
            lock_seconds = min(
                BASE_LOCK_SECONDS * 2 ** (excess - 1), MAX_LOCK_SECONDS
            )
            cache.set(
                f"{key}:locked-until",
                now + int(lock_seconds),
                timeout=int(lock_seconds),
            )


def reset_login_attempts(identifier: str, ip: str) -> None:
    for key in _keys(identifier, ip):
        cache.delete(key)
        cache.delete(f"{key}:streak")
        cache.delete(f"{key}:locked-until")


# ---------------------------------------------------------------------------
# The login entry point (FR-058)
# ---------------------------------------------------------------------------


def login(identifier: str, password: str, ip: str) -> tuple[bool, User | None]:
    """Authenticate with enumeration-resistant, progressively locked checks.

    Ordering guarantees the identical-response property (T-0405):

    * BOTH the lock check and the credential check run on every call — the
      lock check never short-circuits the password verify, so timing cannot
      reveal which of the two failed;
    * unknown emails STILL run the expensive dummy hash (Django does this
      inside ``authenticate``) and still consume attempts, so hammering a
      mailbox list is throttled per identifier and per IP;
    * success clears both scopes' counters.
    """
    identifier = (identifier or "").strip().lower()
    locked = is_locked_out(identifier, ip)
    user = authenticate(email=identifier, password=password)
    if user is not None and user.is_active and not locked:
        reset_login_attempts(identifier, ip)
        return True, user
    if user is None or not user.is_active or not locked:
        # Count genuine credential failures only: a real user retrying their
        # correct password while the lock is displayed does NOT extend the
        # streak or the lock.
        record_failed_login(identifier, ip)
    return False, None
