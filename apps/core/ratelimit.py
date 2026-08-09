"""Fixed-window rate limiting for public write endpoints (T-1707, threat T-14).

Login has its own progressive-lockout scheme in ``apps.accounts.services``,
because a credential guess deserves an escalating penalty. Everything else here
is abuse rather than attack — coupon probing, review spam, contact-form floods,
newsletter bombing — and a flat ceiling per window is the right shape for it.

Two design choices are deliberate:

* **Keys are hashed.** A cache key derived from a raw email would put personal
  data into the cache backend, where it outlives the request and is trivially
  dumped (NFR-012).
* **Exceeding a limit is never an oracle.** The caller decides what to say, and
  every caller here says the same thing whether or not the limit was hit —
  otherwise the limiter becomes a way to enumerate what exists.
"""

from __future__ import annotations

import hashlib

from django.core.cache import cache

#: endpoint -> (max attempts, window seconds)
LIMITS: dict[str, tuple[int, int]] = {
    # Coupon probing is how an attacker discovers valid codes.
    "coupon": (10, 300),
    # A review is a considered act; nobody writes ten in five minutes.
    "review": (5, 3600),
    # Contact forms are the classic spam relay.
    "contact": (5, 3600),
    # Newsletter sign-ups are used to mail-bomb a third party.
    "newsletter": (5, 3600),
}


def _key(scope: str, identifier: str) -> str:
    digest = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:32]
    return f"zakey:rl:{scope}:{digest}"


def allow(scope: str, identifier: str) -> bool:
    """Consume one attempt. ``False`` once the window's ceiling is passed.

    Fails **open** on a cache error rather than closed: a broken cache must not
    take the shop offline. The trade is deliberate and narrow — these endpoints
    all have a second line of defence (validation, CSRF, uniqueness).
    """
    limit, window = LIMITS[scope]
    key = _key(scope, identifier or "anonymous")
    try:
        added = cache.add(key, 1, timeout=window)
        count = 1 if added else cache.incr(key)
    except ValueError:
        # The key expired between add() and incr(); treat as a fresh window.
        cache.set(key, 1, timeout=window)
        count = 1
    except Exception:  # pragma: no cover - defensive
        return True
    return count <= limit


def remaining(scope: str, identifier: str) -> int:
    limit, _ = LIMITS[scope]
    used = cache.get(_key(scope, identifier or "anonymous"), 0)
    try:
        return max(limit - int(used), 0)
    except (TypeError, ValueError):  # pragma: no cover - defensive
        return limit


def reset(scope: str, identifier: str) -> None:
    cache.delete(_key(scope, identifier or "anonymous"))
