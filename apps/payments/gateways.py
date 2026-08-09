"""Payment provider boundary (T-1103, FR-070, FR-079).

**No real payment provider is integrated, and none may be added here.** This
module defines the *shape* a provider would plug into, and ships the two
implementations the approved launch scope actually needs:

* :class:`CODGateway` — cash collected by the courier on delivery;
* :class:`ManualGateway` — a transfer or wallet payment that staff reconcile by
  hand and record after the fact.

Neither talks to a network. Both are complete, honest implementations of how
ZAKEY takes money today, not stubs pretending a gateway exists.

The abstraction earns its place by making the boundary explicit: a future
provider implements :class:`PaymentGateway`, and everything that decides
*whether* money moved keeps living in ``services.py`` where it can be audited.
No gateway may write a ``Payment`` row itself.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import PaymentMethod, PaymentState


@dataclass(frozen=True)
class GatewayResult:
    """What a gateway reports back. Deliberately small.

    ``state`` is a *proposed* state; the service layer validates it against the
    payment state machine before anything is written, so a misbehaving gateway
    cannot drive a payment into an impossible state.
    """

    state: str
    reference: str = ""
    note: str = ""

    def __post_init__(self):
        if self.state not in PaymentState.values:
            raise ValidationError(f"Unknown payment state from gateway: {self.state!r}")


class PaymentGateway(abc.ABC):
    """The contract a payment method's handler must satisfy."""

    #: Matches ``PaymentMethod.code``.
    code: str = ""

    @abc.abstractmethod
    def authorise(self, *, order, amount: Decimal, reference: str = "") -> GatewayResult:
        """Begin taking ``amount`` for ``order``."""

    @abc.abstractmethod
    def capture(self, payment, *, reference: str = "") -> GatewayResult:
        """Confirm the money has actually been received."""

    def cancel(self, payment, *, reason: str = "") -> GatewayResult:
        return GatewayResult(state=PaymentState.CANCELLED, note=reason)

    def refund(self, payment, amount: Decimal, *, reason: str = "") -> GatewayResult:
        """Return ``amount``. Offline methods settle out of band."""
        return GatewayResult(state=PaymentState.CAPTURED, note=reason)

    @property
    def is_external(self) -> bool:
        """True only for a real remote provider. Nothing here is."""
        return False


class CODGateway(PaymentGateway):
    """Cash on delivery (FR-071).

    Nothing is captured at checkout: the courier collects, and staff record the
    capture afterwards. The payment therefore starts — and legitimately stays —
    ``pending`` until someone with the right permission says otherwise, which is
    why an order must never be treated as paid just because it exists.
    """

    code = "payment-cod"

    def authorise(self, *, order, amount: Decimal, reference: str = "") -> GatewayResult:
        return GatewayResult(
            state=PaymentState.PENDING,
            reference=reference,
            note="تحصيل عند الاستلام — لم يُحصّل بعد.",
        )

    def capture(self, payment, *, reference: str = "") -> GatewayResult:
        return GatewayResult(
            state=PaymentState.CAPTURED,
            reference=reference,
            note="تم تحصيل المبلغ عند التسليم.",
        )


class ManualGateway(PaymentGateway):
    """Bank transfer / mobile wallet, reconciled by a human (FR-079).

    The customer pays out of band and staff record it against the order. The
    provider reference is whatever the operator was given — a transfer id, a
    wallet transaction number — and is stored verbatim as evidence, never
    interpreted as proof by itself.
    """

    code = "manual"

    def authorise(self, *, order, amount: Decimal, reference: str = "") -> GatewayResult:
        return GatewayResult(
            state=PaymentState.PENDING,
            reference=reference,
            note="بانتظار تأكيد التحويل من الفريق.",
        )

    def capture(self, payment, *, reference: str = "") -> GatewayResult:
        if not reference:
            raise ValidationError("أدخل مرجع التحويل قبل تأكيد التحصيل.")
        return GatewayResult(
            state=PaymentState.CAPTURED,
            reference=reference,
            note="تم تأكيد التحويل يدويًا.",
        )


#: Every method that is not COD settles manually today. Keyed lookup rather than
#: a registry decorator so the set of live gateways is readable at a glance.
_GATEWAYS: dict[str, PaymentGateway] = {
    CODGateway.code: CODGateway(),
}
_MANUAL = ManualGateway()


def gateway_for(method: PaymentMethod) -> PaymentGateway:
    """The handler for a payment method.

    Raises for a method that is displayed but not connected to anything — the
    storefront already refuses those at checkout, and this is the second refusal
    that stops one being taken by another route (FR-072).
    """
    if method.collects_on_delivery:
        return _GATEWAYS[CODGateway.code]
    if method.is_manual:
        return _MANUAL
    if method.is_integrated:
        raise ValidationError(
            f"طريقة الدفع «{method.label}» معلّمة كمتصلة بمزود، ولا يوجد تكامل "
            "مع أي مزود دفع في هذا الإصدار."
        )
    raise ValidationError(f"طريقة الدفع «{method.label}» غير متاحة حاليًا.")
