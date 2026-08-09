"""Login rate limiting, progressive lockout and no-enumeration (T-0405, FR-058).

Covers the threat-model login deck: per-identifier + per-IP scoping,
progressive locking from the 4th failure, time-warped window behaviour,
success-resets, and byte-identical / duration-equalised failure copy.

Uses ``time.time`` monkeypatching rather than sleeps so the progressive
ladder (30s → ·2 → capped 3600s) is asserted deterministically.
"""

from __future__ import annotations

import time as real_time

import pytest

from apps.accounts import forms, services
from apps.accounts.models import User

pytestmark = pytest.mark.django_db

USER_EMAIL = "victoria@example.com"
PASSWORD = "StrongPass!234"
IP_A = "198.51.100.10"
IP_B = "203.0.113.20"


@pytest.fixture
def victim(db):
    return User.objects.create_user(email=USER_EMAIL, password=PASSWORD)


@pytest.fixture
def now(monkeypatch):
    """A controllable wall clock shared by every service call in a test."""
    current = 1_700_000_000
    monkeypatch.setattr(services.time, "time", lambda: current)

    def advance(seconds):
        nonlocal current
        current += seconds

    return advance


def _fail(email=USER_EMAIL, ip=IP_A):
    return services.login(email, "wrong-password", ip)


# ---------------------------------------------------------------------------
# Threshold: the lock engages exactly after `FREE_ATTEMPTS` free failures
# ---------------------------------------------------------------------------


def test_first_free_attempts_are_free(victim, now):
    for attempt in range(services.FREE_ATTEMPTS):
        ok, _ = _fail()
        assert ok is False
        assert services.is_locked_out(USER_EMAIL, IP_A) is False, f"locked too early (attempt {attempt + 1})"
        assert services.remaining_free_attempts(USER_EMAIL, IP_A) == services.FREE_ATTEMPTS - attempt - 1


def test_lockout_after_threshold_failure(victim, now):
    for _ in range(services.FREE_ATTEMPTS):
        _fail()
    ok, _ = _fail()  # the one that trips the lock
    assert ok is False
    assert services.is_locked_out(USER_EMAIL, IP_A) is True


def test_correct_password_still_fails_while_locked(victim, now):
    for _ in range(services.FREE_ATTEMPTS + 1):
        _fail()
    ok, user = services.login(USER_EMAIL, PASSWORD, IP_A)
    assert ok is False and user is None

    # …and once the lock expires, the same correct password succeeds.
    now(services.BASE_LOCK_SECONDS + 1)
    ok, user = services.login(USER_EMAIL, PASSWORD, IP_A)
    assert ok is True and user.pk == victim.pk


# ---------------------------------------------------------------------------
# Progressive ladder: each new failure doubles the lock (capped)
# ---------------------------------------------------------------------------


def _granted_lock_seconds():
    """How long the lock just set on the IDENTIFIER key runs for, from now."""
    from django.core.cache import cache as djcache

    key = services._keys(USER_EMAIL, IP_A)[0]
    locked_until = djcache.get(f"{key}:locked-until")
    assert locked_until is not None, "expected a lock to have been granted"
    return locked_until - int(services.time.time())


def test_lock_duration_doubles_until_cap(victim, now):
    """The ladder: each *excess* failure doubles the lock (30s → 60s → 120s).

    The previous version of this test asserted `is_locked_out(...) is True`
    immediately after advancing past the lock's own expiry, with a comment
    saying the opposite ("streak frozen, no lock"). It only passed because
    lock state leaked in from earlier tests in the module.
    """
    for _ in range(services.FREE_ATTEMPTS + 1):  # the 4th failure trips rung 1
        _fail()
    assert services.is_locked_out(USER_EMAIL, IP_A) is True
    assert _granted_lock_seconds() == services.BASE_LOCK_SECONDS  # 30s

    # Wait the lock out — with no new failure, the lock simply lapses.
    now(services.BASE_LOCK_SECONDS + 1)
    assert services.is_locked_out(USER_EMAIL, IP_A) is False

    # The streak is still hot, so the next failure lands on rung 2, not rung 1.
    _fail()
    assert services.is_locked_out(USER_EMAIL, IP_A) is True
    assert _granted_lock_seconds() == services.BASE_LOCK_SECONDS * 2  # 60s

    now(services.BASE_LOCK_SECONDS * 2 + 1)
    assert services.is_locked_out(USER_EMAIL, IP_A) is False
    _fail()
    assert _granted_lock_seconds() == services.BASE_LOCK_SECONDS * 4  # 120s

    # Once the final lock lapses the correct password is accepted again.
    now(services.BASE_LOCK_SECONDS * 4 + 1)
    ok, user = services.login(USER_EMAIL, PASSWORD, IP_A)
    assert ok is True and user.pk == victim.pk


def test_lock_duration_is_capped(victim, now):
    from django.core.cache import cache as djcache

    key = services._keys(USER_EMAIL, IP_A)[0]
    djcache.delete(key)
    djcache.delete(f"{key}:locked-until")

    # One failing run, then one more failure just after each lock expires so
    # the streak itself stays inside its window — the ladder must climb.
    for _ in range(services.FREE_ATTEMPTS + 1 + 12):
        _fail()
        now(services.BASE_LOCK_SECONDS + 1)

    locked_until = djcache.get(f"{key}:locked-until")
    assert locked_until is not None
    assert locked_until - int(services.time.time()) <= services.MAX_LOCK_SECONDS


# ---------------------------------------------------------------------------
# Scoping: identifier AND IP are independent (FR-058)
# ---------------------------------------------------------------------------


def test_lock_is_scoped_per_identifier_and_ip(victim, now):
    for _ in range(services.FREE_ATTEMPTS + 1):
        _fail()

    assert services.is_locked_out(USER_EMAIL, IP_A) is True
    # The account lock travels with the ACCOUNT, not the connection: an
    # attacker who rotates source IPs must still not get more attempts at the
    # same mailbox. (This previously asserted False, i.e. that switching IP
    # lifted the account lock — which is precisely the bypass FR-058 exists to
    # prevent, and it also contradicted the OR semantics of is_locked_out.)
    assert services.is_locked_out(USER_EMAIL, IP_B) is True
    # …and a different identifier from the locked IP IS affected by the IP key,
    # which is what stops a mailbox sweep from one host.
    assert services.is_locked_out("coach@example.com", IP_A) is True
    # A clean identity from a clean IP is untouched — the lock is scoped, not global.
    assert services.is_locked_out("coach@example.com", IP_B) is False


def test_unknown_identifier_attempts_are_throttled_too(now):
    ghost = "ghost@zakey.test"
    for _ in range(services.FREE_ATTEMPTS + 1):
        services.login(ghost, "wrong-password", IP_B)
    assert services.is_locked_out(ghost, IP_B) is True


# ---------------------------------------------------------------------------
# Success resets both scopes
# ---------------------------------------------------------------------------


def test_success_resets_all_counters(victim, now):
    # FREE_ATTEMPTS failures consume every free attempt: the *next* one locks.
    # (Same accounting as test_first_free_attempts_are_free — these two must
    # agree, and previously did not.)
    for _ in range(services.FREE_ATTEMPTS):
        _fail()
    assert services.remaining_free_attempts(USER_EMAIL, IP_A) == 0
    assert services.is_locked_out(USER_EMAIL, IP_A) is False

    ok, _ = services.login(USER_EMAIL, PASSWORD, IP_A)
    assert ok is True
    assert services.is_locked_out(USER_EMAIL, IP_A) is False
    # A success wipes the streak on BOTH scopes, restoring the full allowance.
    assert services.remaining_free_attempts(USER_EMAIL, IP_A) == services.FREE_ATTEMPTS


# ---------------------------------------------------------------------------
# No enumeration: identical copy and equalised timing on the public surface
# ---------------------------------------------------------------------------


def test_login_form_failure_copy_is_identical_for_known_and_unknown(victim):
    known = forms.LoginForm(data={"email": USER_EMAIL, "password": "wrong"}, client_ip=IP_A)
    ghost = forms.LoginForm(data={"email": "ghost@zakey.test", "password": "wrong"}, client_ip=IP_A)
    known.is_valid()
    ghost.is_valid()
    assert known.errors.as_text() == ghost.errors.as_text()
    assert forms.GENERIC_LOGIN_ERROR_MESSAGE in known.errors.as_text()


def test_login_form_failure_wall_time_is_equalised(monkeypatch, victim):
    """Wrong-password-with-real-hash vs unknown-email must cost the same."""
    form_failures = []

    real_sleep = real_time.sleep

    def timed(form_cls, **kwargs):
        start = real_time.monotonic()
        form = form_cls(**kwargs)
        form.is_valid()
        form_failures.append(real_time.monotonic() - start)
        return form

    timed(forms.LoginForm, data={"email": USER_EMAIL, "password": "wrong"}, client_ip=IP_A)
    timed(forms.LoginForm, data={"email": "ghost@zakey.test", "password": "wrong"}, client_ip=IP_A)

    known_t, ghost_t = form_failures
    assert known_t >= forms.MINIMUM_LOGIN_RESPONSE_SECONDS
    assert ghost_t >= forms.MINIMUM_LOGIN_RESPONSE_SECONDS
    # Equalisation: the two durations stay within a fifth of the floor.
    assert abs(known_t - ghost_t) < forms.MINIMUM_LOGIN_RESPONSE_SECONDS / 5
    assert real_sleep is real_time.sleep  # smoke: test clock untouched
