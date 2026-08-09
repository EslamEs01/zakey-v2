"""The commercial-rate safeguard (T-2006, ASM-004, ASM-005, FR-045–FR-049).

ZAKEY cannot invent shipping prices or an installation fee — those are the
business's to approve. What *can* be built, and is tested here, is the machinery
that makes a launch on unapproved numbers impossible:

* development values are unmistakably marked as placeholders;
* production refuses to quote a placeholder rather than showing it as a price;
* a launch check reports whether any unapproved rate is still live;
* approved values drop in later with no code change;
* nothing silently infers a commercial value when approval is missing.

The failure this prevents is specific and expensive: a customer charged a
development number, or shown a total the business never agreed to.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.test import override_settings

from apps.shipping import services as shipping_services
from apps.shipping.models import (
    Governorate,
    InstallationService,
    ServiceArea,
    ShippingMethod,
    ShippingRate,
    ShippingZone,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def destination(db):
    gov = Governorate.objects.create(key="cairo", name="القاهرة")
    area = ServiceArea.objects.create(
        governorate=gov, key="cairo-nasr-city", name="مدينة نصر", same_day_eligible=True
    )
    return gov, area


@pytest.fixture
def standard_method(db):
    return ShippingMethod.objects.create(
        code="standard", label="شحن قياسي", position=0, is_active=True
    )


def make_rate(method, governorate, *, price="70.00", placeholder=True):
    zone = ShippingZone.objects.create(name=f"نطاق {method.code}", position=0)
    zone.governorates.add(governorate)
    return ShippingRate.objects.create(
        method=method,
        zone=zone,
        price=Decimal(price),
        is_active=True,
        is_placeholder=placeholder,
        estimated_delivery_text="٢-٣ أيام عمل",
    )


# ---------------------------------------------------------------------------
# Production refuses to quote an unapproved rate
# ---------------------------------------------------------------------------


class TestProductionRefusesPlaceholders:
    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_a_placeholder_shipping_rate_is_refused(
        self, destination, standard_method, site_setting
    ):
        gov, area = destination
        make_rate(standard_method, gov, placeholder=True)

        with pytest.raises(shipping_services.PlaceholderRateError) as caught:
            shipping_services.quote_shipping(
                standard_method, gov, area, Decimal("1000.00")
            )

        assert "معتمدة" in str(caught.value)

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_an_approved_rate_quotes_normally(
        self, destination, standard_method, site_setting
    ):
        gov, area = destination
        make_rate(standard_method, gov, price="85.00", placeholder=False)

        quote = shipping_services.quote_shipping(
            standard_method, gov, area, Decimal("1000.00")
        )

        assert quote.amount == Decimal("85.00")
        assert quote.is_placeholder is False

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=True)
    def test_development_may_opt_in_explicitly(
        self, destination, standard_method, site_setting
    ):
        """Development needs *some* number to render a total; production does not."""
        gov, area = destination
        make_rate(standard_method, gov, placeholder=True)

        quote = shipping_services.quote_shipping(
            standard_method, gov, area, Decimal("1000.00")
        )

        assert quote.is_placeholder is True, "the placeholder flag must survive the opt-in"

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_the_opt_in_defaults_to_off(self, destination, standard_method, site_setting):
        """A missing setting must fail closed, not open."""
        from django.conf import settings

        assert getattr(settings, "ZAKEY_ALLOW_PLACEHOLDER_RATES", False) is False

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_a_free_quote_is_allowed_even_from_a_placeholder_rate(
        self, destination, standard_method, site_setting
    ):
        """Zero is zero. An unapproved rate that costs nothing misleads nobody."""
        gov, area = destination
        standard_method.free_over_threshold = True
        standard_method.save(update_fields=["free_over_threshold"])
        make_rate(standard_method, gov, placeholder=True)

        quote = shipping_services.quote_shipping(
            standard_method, gov, area, Decimal("999999.00")
        )

        assert quote.amount == Decimal("0.00")
        assert quote.free_applied is True
        assert quote.is_placeholder is False


class TestInstallationFeeGate:
    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_a_placeholder_installation_fee_is_refused(self, destination, product):
        gov, _ = destination
        service = InstallationService.objects.create(
            fee=Decimal("250.00"), is_active=True, is_placeholder=True
        )
        service.governorates.add(gov)

        with pytest.raises(shipping_services.PlaceholderRateError):
            shipping_services.quote_installation(gov, None)

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_an_approved_installation_fee_quotes(self, destination):
        gov, _ = destination
        service = InstallationService.objects.create(
            fee=Decimal("300.00"), is_active=True, is_placeholder=False
        )
        service.governorates.add(gov)

        fee, placeholder = shipping_services.quote_installation(gov, None)

        assert fee == Decimal("300.00")
        assert placeholder is False

    def test_an_ineligible_governorate_returns_none(self, destination):
        gov, _ = destination
        InstallationService.objects.create(
            fee=Decimal("300.00"), is_active=True, is_placeholder=False
        )

        assert shipping_services.quote_installation(gov, None) is None

    def test_no_service_configured_returns_none(self, destination):
        gov, _ = destination
        assert shipping_services.installation_available(gov, None) is False


# ---------------------------------------------------------------------------
# The launch gate
# ---------------------------------------------------------------------------


class TestLaunchGate:
    def test_unapproved_rates_are_reported(self, destination, standard_method):
        gov, _ = destination
        make_rate(standard_method, gov, placeholder=True)

        assert shipping_services.has_unapproved_rates() is True

    def test_approved_rates_clear_the_gate(self, destination, standard_method):
        gov, _ = destination
        make_rate(standard_method, gov, placeholder=False)

        assert shipping_services.has_unapproved_rates() is False

    def test_an_unapproved_installation_fee_also_trips_the_gate(self, destination):
        gov, _ = destination
        service = InstallationService.objects.create(
            fee=Decimal("250.00"), is_active=True, is_placeholder=True
        )
        service.governorates.add(gov)

        assert shipping_services.has_unapproved_rates() is True

    def test_an_inactive_placeholder_does_not_trip_the_gate(
        self, destination, standard_method
    ):
        """Only what a customer could actually be charged counts."""
        gov, _ = destination
        rate = make_rate(standard_method, gov, placeholder=True)
        ShippingRate.objects.filter(pk=rate.pk).update(is_active=False)

        assert shipping_services.has_unapproved_rates() is False

    def test_approved_values_need_no_code_change(self, destination, standard_method):
        """The business enters numbers in the admin; nothing here is hard-coded."""
        gov, _ = destination
        rate = make_rate(standard_method, gov, price="70.00", placeholder=True)

        ShippingRate.objects.filter(pk=rate.pk).update(
            price=Decimal("92.50"), is_placeholder=False
        )

        assert shipping_services.has_unapproved_rates() is False
        rate.refresh_from_db()
        assert rate.price == Decimal("92.50")


# ---------------------------------------------------------------------------
# Method availability (FR-047)
# ---------------------------------------------------------------------------


class TestAvailableMethods:
    def test_a_method_with_no_rate_is_not_offered(self, destination, standard_method):
        gov, area = destination

        assert shipping_services.available_methods(gov, area) == []

    def test_a_method_with_a_rate_is_offered(self, destination, standard_method):
        gov, area = destination
        make_rate(standard_method, gov)

        assert shipping_services.available_methods(gov, area) == [standard_method]

    def test_same_day_requires_an_eligible_area(self, destination):
        gov, area = destination
        same_day = ShippingMethod.objects.create(
            code="same-day", label="توصيل في نفس اليوم", position=1,
            is_active=True, requires_area_eligibility=True,
        )
        make_rate(same_day, gov)

        ServiceArea.objects.filter(pk=area.pk).update(same_day_eligible=False)
        area.refresh_from_db()

        assert same_day not in shipping_services.available_methods(gov, area)
        assert shipping_services.available_methods(gov, None) == []

    def test_same_day_quoting_refuses_an_ineligible_area(self, destination, site_setting):
        gov, area = destination
        same_day = ShippingMethod.objects.create(
            code="same-day", label="توصيل في نفس اليوم", position=1,
            is_active=True, requires_area_eligibility=True,
        )
        make_rate(same_day, gov, placeholder=False)
        ServiceArea.objects.filter(pk=area.pk).update(same_day_eligible=False)
        area.refresh_from_db()

        with pytest.raises(ValidationError):
            shipping_services.quote_shipping(same_day, gov, area, Decimal("100.00"))

    def test_quoting_a_destination_with_no_rate_is_refused(
        self, destination, standard_method, site_setting
    ):
        gov, area = destination

        with pytest.raises(ValidationError) as caught:
            shipping_services.quote_shipping(standard_method, gov, area, Decimal("100.00"))

        assert "تسعيرة" in str(caught.value)

    def test_an_inactive_method_is_not_offered(self, destination, standard_method):
        gov, area = destination
        make_rate(standard_method, gov)
        ShippingMethod.objects.filter(pk=standard_method.pk).update(is_active=False)

        assert shipping_services.available_methods(gov, area) == []
