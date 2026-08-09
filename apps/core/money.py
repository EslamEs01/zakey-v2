"""Money rules for ZAKEY (FR-040, FR-042, FR-043, INV-011, INV-012).

Two rules matter more than anything else here:

1. Every monetary value is a ``Decimal``. Binary floating point is never used for
   money, anywhere (INV-012).
2. Catalogue prices are **VAT-inclusive**. VAT is *extracted* from a gross
   amount, never added on top. This is not a preference - it is what the
   approved storefront already does::

       // static/src/js/pages/cart.js:58
       const vat = Math.round((total * fixture.site.vatRate) / (1 + fixture.site.vatRate));

   ``total x r / (1 + r)`` is the extraction formula. Adding VAT instead would
   raise every displayed price by 14% and break the approved visual contract.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MONEY_QUANTUM = Decimal("0.01")
DISPLAY_QUANTUM = Decimal("1")
ZERO = Decimal("0.00")


class MoneyError(ValueError):
    """Raised when a value cannot be treated as money."""


def to_decimal(value: object) -> Decimal:
    """Coerce to Decimal, refusing float outright (INV-012)."""
    if isinstance(value, Decimal):
        return value
    if isinstance(value, float):
        raise MoneyError(
            "Refusing to build money from a float; use Decimal or str (INV-012)."
        )
    if isinstance(value, (int, str)):
        try:
            return Decimal(value)
        except InvalidOperation as exc:  # pragma: no cover - defensive
            raise MoneyError(f"Cannot interpret {value!r} as money.") from exc
    raise MoneyError(f"Unsupported money type {type(value).__name__}.")


def quantize_money(value: object) -> Decimal:
    """Round to 2 decimal places, ROUND_HALF_UP, for storage (FR-043)."""
    return to_decimal(value).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)


def quantize_display(value: object) -> Decimal:
    """Round to 0 decimal places for display.

    Matches ``Intl.NumberFormat(..., {maximumFractionDigits: 0})`` used at
    cart.js:6, checkout.js:11 and wishlist.js:6, and ``currency.decimalPlaces: 0``
    in the approved fixture.
    """
    return to_decimal(value).quantize(DISPLAY_QUANTUM, rounding=ROUND_HALF_UP)


def extract_vat(gross: object, rate: object) -> Decimal:
    """Return the VAT contained *within* a gross amount.

    ``vat = gross * rate / (1 + rate)``. At the 14% Egyptian rate this is
    ``gross * 14 / 114``. The result is a component of ``gross``, never an
    addition to it (INV-011).
    """
    gross_amount = to_decimal(gross)
    vat_rate = to_decimal(rate)
    if vat_rate < 0:
        raise MoneyError("VAT rate cannot be negative.")
    if vat_rate == 0:
        return ZERO
    return quantize_money(gross_amount * vat_rate / (Decimal("1") + vat_rate))


def net_of_vat(gross: object, rate: object) -> Decimal:
    """The amount remaining once the contained VAT is removed."""
    gross_amount = quantize_money(gross)
    return quantize_money(gross_amount - extract_vat(gross_amount, rate))


def line_total(unit_price: object, quantity: int) -> Decimal:
    """Quantize the line before summing so displayed rows add up (FR-043)."""
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        raise MoneyError("Quantity must be an int.")
    if quantity < 0:
        raise MoneyError("Quantity cannot be negative.")
    return quantize_money(to_decimal(unit_price) * Decimal(quantity))


def percentage_of(amount: object, percent: object) -> Decimal:
    """A percentage of an amount, e.g. a 5% coupon (cart.js:56)."""
    return quantize_money(to_decimal(amount) * to_decimal(percent) / Decimal("100"))


def format_egp(value: object, label: str = "ج.م") -> str:
    """Render for the storefront: integer EGP followed by the Arabic label."""
    return f"{quantize_display(value):,.0f} {label}"
