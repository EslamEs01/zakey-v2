"""Payment and refund services (T-1102 – T-1108, FR-070 – FR-079, INV-004).

Every money movement passes through here. The rules that make it safe:

* **Amounts come from the order, never from a request.** ``record_payment``
  takes the amount it is given but refuses anything that would over-pay the
  order, so a tampered admin form cannot invent money.
* **State changes are validated against the machine**, not assigned. A captured
  payment can never go back to pending or on to failed.
* **Refunds are bounded by a locked read.** ``Σ refunds ≤ captured`` is checked
  under ``select_for_update`` so two concurrent refunds cannot both pass a stale
  check (INV-004).
* **Replays are absorbed.** ``idempotency_key`` on the payment and
  ``provider_event_id`` on the event are both unique; a repeat resolves to the
  original row instead of creating a second one.
* **Card data is never accepted, stored or logged.** Nothing in this module has
  a field for one.
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.money import ZERO, quantize_money

from .gateways import gateway_for
from .models import (
    ALLOWED_PAYMENT_TRANSITIONS,
    Payment,
    PaymentEvent,
    PaymentState,
    Refund,
    RefundState,
)


class InvalidPaymentTransition(ValidationError):
    def __init__(self, current: str, target: str):
        super().__init__(f"لا يمكن الانتقال من «{current}» إلى «{target}».")
        self.current = current
        self.target = target


class OverRefund(ValidationError):
    """Refunding more than was captured (INV-004)."""


def _transition(payment: Payment, target: str) -> None:
    if target != payment.state and target not in ALLOWED_PAYMENT_TRANSITIONS.get(
        payment.state, frozenset()
    ):
        raise InvalidPaymentTransition(payment.state, target)
    payment.state = target


def _record_event(payment: Payment, event_type: str, *, note: str = "", provider_event_id: str = "", payload=None) -> PaymentEvent | None:
    """Append one immutable event. A duplicate provider id is a no-op.

    Only a digest of the payload is stored. A provider body can contain
    cardholder data, and keeping it would put that in our database and our logs
    (FR-077, FR-078).
    """
    digest = ""
    if payload is not None:
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
    try:
        with transaction.atomic():
            return PaymentEvent.objects.create(
                payment=payment,
                event_type=event_type,
                provider_event_id=provider_event_id or None,
                payload_digest=digest,
                note=note[:255],
            )
    except IntegrityError:
        # Replayed callback: the unique provider_event_id already exists.
        return None


# ---------------------------------------------------------------------------
# Taking money
# ---------------------------------------------------------------------------


@transaction.atomic
def record_payment(
    *,
    order,
    method,
    amount: Decimal,
    idempotency_key: str,
    reference: str = "",
    actor=None,
) -> Payment:
    """Open a payment attempt against ``order`` (FR-070, FR-073).

    Safe to replay: the same ``idempotency_key`` returns the original attempt.
    """
    existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        return existing

    amount = quantize_money(amount)
    if amount <= ZERO:
        raise ValidationError("مبلغ الدفعة يجب أن يكون أكبر من صفر.")

    outstanding = amount_outstanding(order)
    if amount > outstanding:
        raise ValidationError(
            f"المبلغ يتجاوز المتبقي على الطلب ({outstanding:.2f} ج.م)."
        )

    gateway = gateway_for(method)
    result = gateway.authorise(order=order, amount=amount, reference=reference)

    try:
        with transaction.atomic():
            payment = Payment.objects.create(
                order=order,
                method=method,
                amount=amount,
                currency=order.currency if hasattr(order, "currency") else "EGP",
                state=PaymentState.PENDING,
                provider_reference=result.reference,
                idempotency_key=idempotency_key,
                recorded_by=actor,
            )
    except IntegrityError:
        winner = Payment.objects.filter(idempotency_key=idempotency_key).first()
        if winner is not None:
            return winner
        raise

    if result.state != PaymentState.PENDING:
        _transition(payment, result.state)
        payment.save(update_fields=["state", "updated_at"])

    _record_event(payment, "created", note=result.note)
    _sync_order(order)
    return payment


@transaction.atomic
def capture(payment: Payment, *, reference: str = "", actor=None) -> Payment:
    """Confirm the money was received (FR-073)."""
    locked = Payment.objects.select_for_update().get(pk=payment.pk)
    gateway = gateway_for(locked.method)
    result = gateway.capture(locked, reference=reference or locked.provider_reference)

    _transition(locked, result.state)
    locked.captured_at = timezone.now()
    if result.reference:
        locked.provider_reference = result.reference
    locked.save(update_fields=["state", "captured_at", "provider_reference", "updated_at"])

    _record_event(locked, "captured", note=result.note)
    _audit(locked, "capture", actor, {"state": {"before": payment.state, "after": locked.state}})
    _sync_order(locked.order)
    return locked


@transaction.atomic
def mark_failed(payment: Payment, *, reason: str, actor=None) -> Payment:
    locked = Payment.objects.select_for_update().get(pk=payment.pk)
    _transition(locked, PaymentState.FAILED)
    locked.failed_reason = reason[:255]
    locked.save(update_fields=["state", "failed_reason", "updated_at"])
    _record_event(locked, "failed", note=reason)
    _audit(locked, "fail", actor, {"reason": reason})
    _sync_order(locked.order)
    return locked


@transaction.atomic
def cancel(payment: Payment, *, reason: str = "", actor=None) -> Payment:
    locked = Payment.objects.select_for_update().get(pk=payment.pk)
    _transition(locked, PaymentState.CANCELLED)
    locked.save(update_fields=["state", "updated_at"])
    _record_event(locked, "cancelled", note=reason)
    _audit(locked, "cancel", actor, {"reason": reason})
    _sync_order(locked.order)
    return locked


# ---------------------------------------------------------------------------
# Giving it back (INV-004)
# ---------------------------------------------------------------------------


@transaction.atomic
def refund(payment: Payment, amount: Decimal, *, reason: str, actor=None) -> Refund:
    """Refund ``amount``, never more than remains captured (FR-075, INV-004).

    The payment row is locked before the remaining balance is computed. Two
    concurrent refunds therefore serialise: the second reads the first's result
    and is refused, instead of both passing a check taken before either wrote.
    """
    locked = Payment.objects.select_for_update().get(pk=payment.pk)
    amount = quantize_money(amount)

    if amount <= ZERO:
        raise ValidationError("مبلغ الاسترجاع يجب أن يكون أكبر من صفر.")
    if locked.state not in {PaymentState.CAPTURED, PaymentState.PARTIALLY_REFUNDED}:
        raise ValidationError("لا يمكن استرجاع دفعة غير محصّلة.")

    remaining = locked.refundable_amount
    if amount > remaining:
        raise OverRefund(
            f"الاسترجاع ({amount:.2f}) يتجاوز المتبقي القابل للاسترجاع ({remaining:.2f})."
        )

    gateway = gateway_for(locked.method)
    result = gateway.refund(locked, amount, reason=reason)

    record = Refund.objects.create(
        payment=locked,
        amount=amount,
        reason=reason[:255],
        state=RefundState.COMPLETED,
        provider_reference=result.reference,
        actor=actor,
    )

    # Re-read through the relation so the new row is included.
    locked.refresh_from_db()
    target = (
        PaymentState.REFUNDED
        if locked.refunded_amount >= locked.amount
        else PaymentState.PARTIALLY_REFUNDED
    )
    _transition(locked, target)
    locked.save(update_fields=["state", "updated_at"])

    _record_event(locked, "refunded", note=f"{amount} — {reason}")
    _audit(locked, "refund", actor, {"amount": str(amount), "reason": reason})
    _sync_order(locked.order)
    return record


# ---------------------------------------------------------------------------
# Derivation and reconciliation
# ---------------------------------------------------------------------------


def amount_captured(order) -> Decimal:
    total = ZERO
    for payment in order.payments.all():
        if payment.state in {PaymentState.CAPTURED, PaymentState.PARTIALLY_REFUNDED}:
            total += payment.amount
        elif payment.state == PaymentState.REFUNDED:
            total += payment.amount
    return quantize_money(total)


def amount_refunded(order) -> Decimal:
    return quantize_money(
        sum((payment.refunded_amount for payment in order.payments.all()), ZERO)
    )


def amount_outstanding(order) -> Decimal:
    """What the order still needs, ignoring attempts that never captured."""
    settled = amount_captured(order) - amount_refunded(order)
    return quantize_money(max(ZERO, order.grand_total - settled))


def _sync_order(order) -> str:
    """Payment status is derived from the ledger, never hand-set (FR-073)."""
    from apps.orders.services import recompute_payment_status

    return recompute_payment_status(order)


#: Money movements get their own audit verbs so a finance review can filter on
#: them without reading every generic "update" row.
_AUDIT_ACTIONS = {
    "capture": "PAYMENT_RECORD",
    "fail": "PAYMENT_RECORD",
    "cancel": "PAYMENT_RECORD",
    "refund": "REFUND",
}


def _audit(payment: Payment, action: str, actor, changes: dict) -> None:
    from apps.audit.models import AuditAction
    from apps.audit.services import record_audit

    record_audit(
        actor=actor,
        action=getattr(AuditAction, _AUDIT_ACTIONS[action]),
        obj=payment,
        changes={"payment_action": action, **changes},
    )


def reconcile(order=None) -> list[dict]:
    """Report ledger/order divergence. Mutates nothing (FR-076).

    A reconciliation tool that repairs what it finds hides the bug that caused
    the divergence, so this one only reports.
    """
    from apps.orders.models import Order

    # Re-read: the caller may hold an instance whose payment_status predates the
    # last write, and reporting that as divergence would be reporting staleness,
    # not a real inconsistency.
    orders = (
        Order.objects.filter(pk=order.pk).prefetch_related("payments__refunds")
        if order is not None
        else Order.objects.prefetch_related("payments__refunds")
    )
    divergences = []
    for candidate in orders:
        captured = amount_captured(candidate)
        refunded = amount_refunded(candidate)
        settled = captured - refunded
        expected = candidate.payment_status
        derived = _derive_status(candidate, captured, refunded)
        if expected != derived:
            divergences.append(
                {
                    "order": candidate.number,
                    "field": "payment_status",
                    "stored": expected,
                    "derived": derived,
                }
            )
        if settled > candidate.grand_total:
            divergences.append(
                {
                    "order": candidate.number,
                    "field": "settled_amount",
                    "stored": str(settled),
                    "derived": str(candidate.grand_total),
                    "note": "الطلب محصّل بأكثر من إجماليه.",
                }
            )
        if refunded > captured:
            divergences.append(
                {
                    "order": candidate.number,
                    "field": "refunded_amount",
                    "stored": str(refunded),
                    "derived": str(captured),
                    "note": "الاسترجاع يتجاوز المحصّل (INV-004).",
                }
            )
    return divergences


def _derive_status(order, captured: Decimal, refunded: Decimal) -> str:
    from apps.orders.models import PaymentStatus

    if captured <= ZERO:
        return PaymentStatus.UNPAID
    if refunded >= captured and refunded > ZERO:
        return PaymentStatus.REFUNDED
    if refunded > ZERO:
        return PaymentStatus.PARTIALLY_REFUNDED
    if captured >= order.grand_total:
        return PaymentStatus.PAID
    return PaymentStatus.PARTIALLY_PAID


# ---------------------------------------------------------------------------
# Provider callbacks (T-1107) — skeleton, no provider connected
# ---------------------------------------------------------------------------


class WebhookRejected(ValidationError):
    pass


def verify_signature(secret: str, raw_body: bytes, signature: str) -> bool:
    """Constant-time HMAC check.

    No provider is connected, so no secret is configured and no caller reaches
    this in production. It exists so the *first* thing a future integration does
    is verify, rather than discovering later that it never did.
    """
    import hmac

    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


@transaction.atomic
def handle_provider_event(payment: Payment, *, provider_event_id: str, event_type: str, payload: dict) -> PaymentEvent | None:
    """Record one provider event exactly once (FR-074).

    Returns ``None`` when the event has already been seen — a replayed callback
    must be a no-op, not a second capture.
    """
    if not provider_event_id:
        raise WebhookRejected("حدث المزود بلا معرف فريد.")
    return _record_event(
        payment,
        event_type,
        provider_event_id=provider_event_id,
        payload=payload,
    )
