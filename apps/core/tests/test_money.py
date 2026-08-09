"""Money rules (FR-040, FR-042, FR-043, INV-011, INV-012)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.core.money import (
    MoneyError,
    extract_vat,
    format_egp,
    line_total,
    net_of_vat,
    percentage_of,
    quantize_display,
    quantize_money,
)

RATE = Decimal("0.14")


class TestVatIsExtractedNotAdded:
    """The single most important money rule in the system (INV-011)."""

    def test_vat_is_a_component_of_the_gross_amount(self):
        gross = Decimal("7490.00")
        vat = extract_vat(gross, RATE)
        # 7490 * 14 / 114 = 919.8245...
        assert vat == Decimal("919.82")
        # The defining property: VAT is INSIDE the price, never added to it.
        assert vat < gross
        assert net_of_vat(gross, RATE) + vat == gross

    def test_matches_the_storefront_formula_exactly(self):
        """Mirrors static/src/js/pages/cart.js:58.

        `Math.round((total * rate) / (1 + rate))` - the storefront rounds to a
        whole pound because it displays 0 decimals.
        """
        for gross in ("2190", "3990", "5000", "7490", "11480"):
            amount = Decimal(gross)
            expected = (amount * RATE / (Decimal("1") + RATE)).quantize(Decimal("1"))
            assert quantize_display(extract_vat(amount, RATE)) == expected

    def test_adding_vat_would_inflate_the_price_by_14_percent(self):
        """Guards against the classic mistake this spec exists to prevent."""
        gross = Decimal("1000.00")
        wrong = gross * RATE  # what "add VAT" would produce
        right = extract_vat(gross, RATE)
        assert right < wrong
        assert right == Decimal("122.81")

    def test_zero_rate_yields_zero(self):
        assert extract_vat(Decimal("100"), Decimal("0")) == Decimal("0.00")

    def test_negative_rate_rejected(self):
        with pytest.raises(MoneyError):
            extract_vat(Decimal("100"), Decimal("-0.1"))


class TestNoBinaryFloatingPoint:
    """INV-012: money is never a float."""

    @pytest.mark.parametrize("bad", [10.5, 0.1, 1e3])
    def test_float_is_refused_everywhere(self, bad):
        for fn in (quantize_money, quantize_display):
            with pytest.raises(MoneyError):
                fn(bad)
        with pytest.raises(MoneyError):
            extract_vat(bad, RATE)
        with pytest.raises(MoneyError):
            line_total(bad, 2)

    def test_decimal_and_str_and_int_accepted(self):
        assert quantize_money(Decimal("10.005")) == Decimal("10.01")
        assert quantize_money("10.004") == Decimal("10.00")
        assert quantize_money(10) == Decimal("10.00")


class TestRounding:
    def test_round_half_up_not_bankers(self):
        # Python's default is ROUND_HALF_EVEN, which would give 10.00 here.
        assert quantize_money("10.005") == Decimal("10.01")
        assert quantize_money("10.015") == Decimal("10.02")

    def test_display_is_zero_decimals(self):
        assert quantize_display("7489.60") == Decimal("7490")
        assert quantize_display("7489.40") == Decimal("7489")

    def test_line_totals_quantize_before_summing(self):
        """So displayed rows always add up to the displayed subtotal (FR-043)."""
        unit = Decimal("33.333")
        lines = [line_total(unit, 3), line_total(unit, 3)]
        assert lines == [Decimal("100.00"), Decimal("100.00")]
        assert sum(lines) == Decimal("200.00")

    def test_quantity_must_be_int(self):
        with pytest.raises(MoneyError):
            line_total(Decimal("10"), 2.5)
        with pytest.raises(MoneyError):
            line_total(Decimal("10"), -1)


class TestCouponMath:
    def test_five_percent_matches_the_prototype_coupon(self):
        """ZAKEYDEMO is 5% (fixture site.couponPrototype.discountRate = 0.05)."""
        assert percentage_of(Decimal("10000.00"), Decimal("5")) == Decimal("500.00")


class TestFormatting:
    def test_renders_integer_egp_with_arabic_label(self):
        assert format_egp(Decimal("7490.00")) == "7,490 ج.م"
        assert format_egp(Decimal("1500.49")) == "1,500 ج.م"
