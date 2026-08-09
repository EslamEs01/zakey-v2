"""Shipping and installation quoting (FR-041, FR-045 – FR-049, FR-062).

The approved storefront contains **no shipping price at all**: `shippingOptions`
carry label/description/eligibility/icon and nothing monetary, and the prototype
total is `subtotal - discount` with shipping rendered as a text label. A real
store cannot render a correct total that way, so shipping and installation are
introduced as configurable, staff-owned money here (ASM-004, ASM-005).

Every quote reports whether it used a development placeholder so the caller can
refuse to show it as a real price in production.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError

from apps.core.money import ZERO, quantize_money

from .models import Governorate, InstallationService, ServiceArea, ShippingMethod, ShippingRate


class PlaceholderRateError(ValidationError):
    """Raised when production would otherwise quote an unapproved price."""


@dataclass(frozen=True)
class ShippingQuote:
    method: ShippingMethod
    amount: Decimal
    label: str
    estimated_delivery: str
    is_placeholder: bool
    free_applied: bool = False

    def as_tuple(self) -> tuple[Decimal, str, bool]:
        return self.amount, self.label, self.is_placeholder


def _guard_placeholder(is_placeholder: bool, what: str) -> None:
    if is_placeholder and not getattr(settings, "ZAKEY_ALLOW_PLACEHOLDER_RATES", False):
        raise PlaceholderRateError(
            f"{what} مضبوط على قيمة تطويرية غير معتمدة. "
            "يجب إدخال الأسعار التجارية المعتمدة قبل التشغيل."
        )


def available_methods(governorate: Governorate, area: ServiceArea | None):
    """Methods offered for this destination (FR-047)."""
    methods = []
    for method in ShippingMethod.objects.filter(is_active=True).order_by("position"):
        if method.requires_area_eligibility:
            if area is None or not area.same_day_eligible:
                continue
        if not ShippingRate.objects.filter(
            method=method, is_active=True, zone__governorates=governorate
        ).exists():
            continue
        methods.append(method)
    return methods


def quote_shipping(
    method: ShippingMethod,
    governorate: Governorate,
    area: ServiceArea | None,
    discounted_subtotal: Decimal,
) -> ShippingQuote:
    """Price one method for one destination."""
    if method.requires_area_eligibility and (area is None or not area.same_day_eligible):
        raise ValidationError("هذه الطريقة غير متاحة للمنطقة المختارة.")

    rate = (
        ShippingRate.objects.filter(
            method=method, is_active=True, zone__governorates=governorate
        )
        .select_related("zone")
        .order_by("zone__position")
        .first()
    )
    if rate is None:
        raise ValidationError("لا توجد تسعيرة شحن لهذه المحافظة.")

    from apps.core.models import SiteSetting

    threshold = SiteSetting.objects.get_solo().free_shipping_threshold
    free_applied = method.free_over_threshold and discounted_subtotal >= threshold
    amount = ZERO if free_applied else quantize_money(rate.price)

    # A free quote costs nothing, so an unapproved rate cannot mislead anyone.
    is_placeholder = rate.is_placeholder and not free_applied
    _guard_placeholder(is_placeholder, "سعر الشحن")

    return ShippingQuote(
        method=method,
        amount=amount,
        label=method.label,
        estimated_delivery=rate.estimated_delivery_text,
        is_placeholder=is_placeholder,
        free_applied=free_applied,
    )


def installation_available(governorate: Governorate, cart) -> bool:
    """Eligible governorate AND every line supports installation (FR-048)."""
    service = InstallationService.objects.filter(is_active=True).first()
    if service is None:
        return False
    if not service.governorates.filter(pk=governorate.pk).exists():
        return False
    if cart is None:
        return True
    lines = cart.lines.select_related("variant__product")
    if not lines.exists():
        return False
    return all(line.variant.product.installation_supported for line in lines)


def quote_installation(governorate: Governorate, cart) -> tuple[Decimal, bool] | None:
    """Return ``(fee, is_placeholder)`` or None when not eligible."""
    if not installation_available(governorate, cart):
        return None
    service = InstallationService.objects.filter(is_active=True).first()
    _guard_placeholder(service.is_placeholder, "رسوم التركيب")
    return quantize_money(service.fee), service.is_placeholder


def has_unapproved_rates() -> bool:
    """Launch gate helper for T-2006 (ASM-004, ASM-005)."""
    return (
        ShippingRate.objects.filter(is_active=True, is_placeholder=True).exists()
        or InstallationService.objects.filter(is_active=True, is_placeholder=True).exists()
    )
