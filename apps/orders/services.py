"""Order creation and transitions (FR-061 – FR-069, INV-002, INV-003, INV-006).

``create_order`` is one atomic transaction covering validation, stock locking,
coupon locking, total recomputation, order write, reservation and redemption.
Any failure rolls everything back and **leaves the cart intact** — a customer
who loses their basket at checkout does not come back.

Two details carry most of the safety:

* **Deterministic lock ordering.** Stock rows are locked in ascending
  ``variant_id`` order, so two carts holding {A, B} and {B, A} cannot deadlock.
* **Insert-then-select idempotency.** A replayed submission hits the unique
  ``idempotency_key`` constraint and returns the original order (INV-002).
"""

from __future__ import annotations

import secrets
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.middleware import get_request_id
from apps.cart.models import CartStatus
from apps.cart.services import price_cart
from apps.core.models import SiteSetting
from apps.core.money import ZERO
from apps.inventory.models import ReservationState, StockItem
from apps.inventory.services import InsufficientStock
from apps.inventory import services as inventory_services

from .models import (
    ALLOWED_TRANSITIONS,
    InvalidTransition,
    Order,
    OrderAddress,
    OrderEvent,
    OrderLine,
    OrderStatus,
    PaymentStatus,
)


class EmptyCart(ValidationError):
    pass


def generate_order_number() -> str:
    """Readable, unique, and not a running counter (FR-065).

    A sequential number would leak order volume to anyone who places two orders.
    """
    prefix = SiteSetting.objects.get_solo().order_number_prefix
    stamp = timezone.now().strftime("%y%m%d")
    suffix = secrets.token_hex(3).upper()
    return f"{prefix}-{stamp}-{suffix}"


@transaction.atomic
def create_order(
    *,
    cart,
    email: str,
    phone: str,
    address_data: dict,
    idempotency_key: str,
    shipping_quote=None,
    installation_quote=None,
    customer=None,
    terms_accepted: bool = False,
    actor=None,
) -> Order:
    """Create one order from a cart. Safe to replay (INV-002)."""

    existing = Order.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        return existing

    if not terms_accepted:
        raise ValidationError("أكد موافقتك على الشروط لإتمام الطلب.")

    lines = list(
        cart.lines.select_related("variant__product", "variant__stock_item").order_by(
            "variant_id"
        )
    )
    if not lines:
        raise EmptyCart("سلتك فارغة.")

    # 1. Lock every stock row in ascending variant_id order (deadlock safety).
    variant_ids = sorted(line.variant_id for line in lines)
    stock_map = {
        item.variant_id: item
        for item in StockItem.objects.select_for_update()
        .filter(variant_id__in=variant_ids)
        .order_by("variant_id")
    }

    for line in lines:
        stock = stock_map.get(line.variant_id)
        if stock is None:
            raise ValidationError(f"لا يوجد رصيد مخزون لـ {line.variant.sku}.")
        if stock.available < line.quantity:
            raise InsufficientStock(line.variant, line.quantity, stock.available)
        if not line.variant.is_active or not line.variant.product.is_published:
            raise ValidationError(f"«{line.variant.product.name}» لم يعد متاحًا للشراء.")

    # 2. Recompute every figure from locked rows. Nothing monetary comes from
    #    the request (FR-034).
    coupon = cart.coupon
    if coupon is not None:
        from apps.promotions.services import validate_coupon

        preliminary = price_cart(cart)
        validate_coupon(coupon, preliminary.subtotal, customer=customer, cart=cart)

    totals = price_cart(
        cart,
        coupon=coupon,
        shipping_quote=shipping_quote,
        installation_quote=installation_quote,
    )
    if totals.has_unavailable:
        names = "، ".join(p.variant.product.name for p in totals.unavailable_lines)
        raise ValidationError(f"لم تعد هذه المنتجات متاحة: {names}")
    if totals.grand_total < ZERO:
        raise ValidationError("إجمالي غير صالح.")

    settings_obj = SiteSetting.objects.get_solo()

    # 3. Create the order. A concurrent replay loses the unique-key race and is
    #    resolved by returning the winner rather than creating a second order.
    try:
        with transaction.atomic():
            order = Order.objects.create(
                number=generate_order_number(),
                customer=customer,
                email=email.strip().lower(),
                phone=phone,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.UNPAID,
                idempotency_key=idempotency_key,
                subtotal=totals.subtotal,
                discount_total=totals.discount_total,
                coupon_code=totals.coupon_code,
                shipping_method_label=totals.shipping_label,
                shipping_total=totals.shipping_total,
                installation_requested=totals.installation_requested,
                installation_total=totals.installation_total,
                vat_amount=totals.vat_amount,
                vat_rate=settings_obj.vat_rate,
                grand_total=totals.grand_total,
                used_placeholder_rates=totals.used_placeholder_rates,
                terms_accepted_at=timezone.now(),
                placed_at=timezone.now(),
            )
    except IntegrityError:
        winner = Order.objects.filter(idempotency_key=idempotency_key).first()
        if winner is not None:
            return winner
        raise

    # 4. Immutable line snapshots (INV-003).
    for priced in totals.lines:
        variant = priced.variant
        image = variant.product.primary_image
        OrderLine.objects.create(
            order=order,
            variant=variant,
            product_name=variant.product.name,
            product_slug=variant.product.slug,
            variant_label=variant.finish_label,
            sku=variant.sku,
            image_path=image.src if image else "",
            unit_price=priced.unit_price,
            quantity=priced.quantity,
            line_total=priced.total,
        )

    OrderAddress.objects.create(order=order, **address_data)

    # 5. Reserve stock for every line.
    for line in lines:
        inventory_services.reserve(line.variant, line.quantity, order=order, actor=actor)

    # 6. Consume the coupon under its own lock.
    if coupon is not None and totals.discount_total > ZERO:
        from apps.promotions.services import redeem

        redeem(coupon, order, totals.discount_total, customer=customer)

    OrderEvent.objects.create(
        order=order,
        event_type="created",
        to_status=OrderStatus.PENDING,
        actor=actor,
        request_id=get_request_id() or "",
    )

    cart.status = CartStatus.CONVERTED
    cart.save(update_fields=["status", "updated_at"])
    return order


@transaction.atomic
def transition(order: Order, target: str, *, actor=None, note: str = "") -> Order:
    """Move an order along an allowed edge only (FR-068, INV-006).

    The current status is re-read **inside** the lock, so two staff members
    clicking different actions produce exactly one winner.
    """
    locked = Order.objects.select_for_update().get(pk=order.pk)
    if target not in ALLOWED_TRANSITIONS.get(locked.status, frozenset()):
        raise InvalidTransition(locked.status, target)

    previous = locked.status
    locked.status = target

    if target == OrderStatus.PROCESSING:
        for reservation in locked.reservations.filter(state=ReservationState.ACTIVE):
            inventory_services.fulfill(reservation, actor=actor)
        from .models import FulfillmentStatus

        locked.fulfillment_status = FulfillmentStatus.FULFILLED

    if target == OrderStatus.CANCELLED:
        for reservation in locked.reservations.filter(state=ReservationState.ACTIVE):
            inventory_services.release(reservation, actor=actor)
        from apps.promotions.services import reverse_redemption

        reverse_redemption(locked)
        locked.cancelled_at = timezone.now()

    locked.save()

    OrderEvent.objects.create(
        order=locked,
        event_type="status_change",
        from_status=previous,
        to_status=target,
        actor=actor,
        note=note,
        request_id=get_request_id() or "",
    )

    from apps.audit.services import record_audit
    from apps.audit.models import AuditAction

    record_audit(
        action=AuditAction.STATUS_CHANGE,
        obj=locked,
        actor=actor,
        changes={"status": {"before": previous, "after": target}},
    )
    return locked


def claimable_guest_orders(profile):
    """Guest orders that *could* be associated with ``profile`` (FR-059).

    Matching is on the email captured at checkout, compared case-insensitively
    because a customer who typed ``Nada@Example.com`` at checkout and
    ``nada@example.com`` at registration is the same person.

    Only unassociated orders are ever returned. An order already belonging to
    somebody is never a candidate, so this can never be used to move an order
    between two accounts.
    """
    return (
        Order.objects.filter(customer__isnull=True, email__iexact=profile.user.email)
        .order_by("created_at")
    )


@transaction.atomic
def associate_guest_orders(profile, *, actor=None) -> int:
    """Attach a registering customer's prior guest orders (FR-059, ASM-002).

    Deliberately **staff-initiated**, never automatic on registration. Guest
    checkout only ever proved control of a basket, not of an inbox — if merely
    registering with an address silently handed over every order ever placed
    with it, anyone could claim a stranger's order history by typing their
    email. A human decides, and the decision is auditable.

    Idempotent: running it twice associates nothing the second time, because
    the first run removed those orders from the claimable set.

    Returns the number of orders newly associated.
    """
    orders = list(claimable_guest_orders(profile).select_for_update())
    if not orders:
        return 0

    from apps.audit.models import AuditAction
    from apps.audit.services import record_audit

    for order in orders:
        order.customer = profile
        order.save(update_fields=["customer", "updated_at"])
        OrderEvent.objects.create(
            order=order,
            event_type="guest_order_association",
            actor=actor,
            request_id=get_request_id() or "",
            note=f"رُبط الطلب بحساب {profile.user.email}",
        )
        record_audit(
            actor,
            AuditAction.UPDATE,
            order,
            {
                "customer": {"before": None, "after": profile.pk},
                "reason": "guest_order_association",
                "email": profile.user.email,
            },
        )
    return len(orders)


def recompute_payment_status(order: Order) -> str:
    """Derive payment status from the ledger; never hand-set (FR-073)."""
    from apps.payments.models import PaymentState

    payments = order.payments.all()
    # REFUNDED belongs here too. Money that was captured and then given back was
    # still captured; excluding it made a fully-refunded order read as UNPAID —
    # indistinguishable from one that never paid at all.
    captured = sum(
        (
            p.amount
            for p in payments
            if p.state
            in {
                PaymentState.CAPTURED,
                PaymentState.PARTIALLY_REFUNDED,
                PaymentState.REFUNDED,
            }
        ),
        Decimal("0.00"),
    )
    refunded = sum((p.refunded_amount for p in payments), Decimal("0.00"))

    if captured <= ZERO:
        status = PaymentStatus.UNPAID
    elif refunded >= captured and refunded > ZERO:
        status = PaymentStatus.REFUNDED
    elif refunded > ZERO:
        status = PaymentStatus.PARTIALLY_REFUNDED
    elif captured >= order.grand_total:
        status = PaymentStatus.PAID
    else:
        status = PaymentStatus.PARTIALLY_PAID

    if order.payment_status != status:
        order.payment_status = status
        order.save(update_fields=["payment_status", "updated_at"])
    return status
