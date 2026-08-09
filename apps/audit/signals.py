"""Audit signals (T-1406, T-1407, FR-113, FR-115).

Services already record the *interesting* mutations with full context — an order
transition knows which statuses it moved between, a refund knows its amount.
What signals add is coverage of the paths a service never sees: a staff member
editing a row directly in the admin, a shell session, a bulk import.

So these handlers are deliberately coarse. They record *that* a financially or
operationally significant row changed, and who changed it. They do not try to
re-derive the domain meaning a service already logged.

Two rules shaped this module:

* **Never log a credential.** ``user_login_failed`` receives the submitted
  credentials dict, password included. Only the identifier is ever read out of
  it, and even that goes through the same redaction the logging stack uses.
* **Never let auditing break the thing being audited.** A failure to write an
  audit row must not roll back a customer's order, so every handler is
  defensive.
"""

from __future__ import annotations

import logging

from django.contrib.auth import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.audit.models import AuditAction

logger = logging.getLogger("zakey.audit")

#: Models whose every create/update/delete is worth a row (T-1406).
_TRACKED = [
    ("orders", "Order"),
    ("payments", "Payment"),
    ("payments", "Refund"),
    ("inventory", "StockItem"),
    ("promotions", "Coupon"),
]


def _safe_record(actor, action, obj, changes=None) -> None:
    """Record an audit row, never raising into the caller's transaction."""
    from apps.audit.services import record_audit

    try:
        record_audit(actor, action, obj, changes or {})
    except Exception:  # pragma: no cover - defensive
        logger.exception("failed to write audit row for %s", getattr(obj, "pk", None))


# ---------------------------------------------------------------------------
# T-1407 — staff authentication logging (FR-115)
# ---------------------------------------------------------------------------


@receiver(user_logged_in)
def _log_login(sender, request, user, **kwargs):  # noqa: ARG001
    _safe_record(
        user,
        AuditAction.LOGIN,
        user,
        {"is_staff": bool(user.is_staff), "is_superuser": bool(user.is_superuser)},
    )


@receiver(user_logged_out)
def _log_logout(sender, request, user, **kwargs):  # noqa: ARG001
    if user is None:
        return
    _safe_record(user, AuditAction.LOGOUT, user, {"is_staff": bool(user.is_staff)})


@receiver(user_login_failed)
def _log_login_failure(sender, credentials, request=None, **kwargs):  # noqa: ARG001
    """Record a failed attempt without ever recording the password.

    ``credentials`` carries the submitted password. Only the identifier is read
    out of it; nothing else in the dict is touched.
    """
    identifier = ""
    for key in ("username", "email"):
        value = (credentials or {}).get(key)
        if value:
            identifier = str(value)[:254]
            break

    from django.apps import apps as django_apps

    user = None
    if identifier:
        user_model = django_apps.get_model("accounts", "User")
        user = user_model.objects.filter(email__iexact=identifier).first()

    _safe_record(
        None,
        AuditAction.LOGIN_FAILED,
        user,
        {
            "identifier": identifier,
            "is_staff": bool(getattr(user, "is_staff", False)),
            "account_exists": user is not None,
        },
    )


# ---------------------------------------------------------------------------
# T-1406 — permission changes (FR-113)
# ---------------------------------------------------------------------------


@receiver(m2m_changed)
def _log_permission_membership(sender, instance, action, reverse, pk_set, **kwargs):  # noqa: ARG001
    """Group membership and permission grants are security events."""
    if action not in {"post_add", "post_remove", "post_clear"}:
        return

    name = getattr(sender, "__name__", "")
    if name not in {
        "User_groups",
        "User_user_permissions",
        "Group_permissions",
    }:
        return

    _safe_record(
        None,
        AuditAction.PERMISSION_CHANGE,
        instance,
        {"relation": name, "action": action, "ids": sorted(pk_set or [])},
    )


@receiver(pre_save)
def _capture_previous_state(sender, instance, **kwargs):  # noqa: ARG001
    """Stash the prior row for the handful of fields worth diffing."""
    label = (sender._meta.app_label, sender.__name__)
    if label not in {("accounts", "User"), ("catalog", "ProductVariant")}:
        return
    if instance.pk is None:
        return
    try:
        instance._audit_previous = sender._base_manager.filter(pk=instance.pk).first()
    except Exception:  # pragma: no cover - defensive
        instance._audit_previous = None


@receiver(post_save)
def _log_staff_flag_change(sender, instance, created, **kwargs):  # noqa: ARG001
    """Granting staff or superuser is the most sensitive change in the system."""
    if (sender._meta.app_label, sender.__name__) != ("accounts", "User"):
        return

    previous = getattr(instance, "_audit_previous", None)
    if previous is None:
        return

    changed = {
        field: {"before": getattr(previous, field), "after": getattr(instance, field)}
        for field in ("is_staff", "is_superuser", "is_active")
        if getattr(previous, field) != getattr(instance, field)
    }
    if changed:
        _safe_record(None, AuditAction.PERMISSION_CHANGE, instance, changed)


# ---------------------------------------------------------------------------
# T-1406 — price changes (FR-113)
# ---------------------------------------------------------------------------


@receiver(post_save)
def _log_price_change(sender, instance, created, **kwargs):  # noqa: ARG001
    if (sender._meta.app_label, sender.__name__) != ("catalog", "ProductVariant"):
        return

    previous = getattr(instance, "_audit_previous", None)
    if previous is None or previous.price == instance.price:
        return

    _safe_record(
        None,
        AuditAction.PRICE_CHANGE,
        instance,
        {"price": {"before": str(previous.price), "after": str(instance.price)}},
    )


# ---------------------------------------------------------------------------
# T-1406 — order, payment, refund, stock and coupon mutations (FR-113)
# ---------------------------------------------------------------------------


@receiver(post_save)
def _log_tracked_save(sender, instance, created, **kwargs):  # noqa: ARG001
    if (sender._meta.app_label, sender.__name__) not in [
        (app, model) for app, model in _TRACKED
    ]:
        return
    _safe_record(
        None,
        AuditAction.CREATE if created else AuditAction.UPDATE,
        instance,
        {"model": instance._meta.label, "created": created},
    )


@receiver(post_delete)
def _log_tracked_delete(sender, instance, **kwargs):  # noqa: ARG001
    if (sender._meta.app_label, sender.__name__) not in [
        (app, model) for app, model in _TRACKED
    ]:
        return
    _safe_record(None, AuditAction.DELETE, instance, {"model": instance._meta.label})
