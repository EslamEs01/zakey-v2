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


# ---------------------------------------------------------------------------
# Same-day eligibility (FR-047)
# ---------------------------------------------------------------------------


class TestSameDayEligibility:
    """Same-day delivery is doubly gated: by the area and by staff.

    Every price here is a development placeholder. The eligibility question is
    independent of the number, and the number is still T-2006 business input.
    """

    def test_same_day_needs_an_eligible_area_and_a_staff_enabled_method(self, destination):
        """FR-047: both gates must be open, and either one closes the offer.

        The same destination is asked four times. It is offered only in the one
        arrangement where staff enabled the method *and* marked the area
        eligible; disabling either half withdraws it, and an address with no
        area at all never gets it.
        """
        gov, area = destination  # the fixture area is same-day eligible
        same_day = ShippingMethod.objects.create(
            code="same-day-fr047",
            label="توصيل في نفس اليوم",
            position=1,
            is_active=True,
            requires_area_eligibility=True,
        )
        make_rate(same_day, gov)

        assert same_day in shipping_services.available_methods(gov, area)

        # Staff switch the method off: eligible area or not, it disappears.
        ShippingMethod.objects.filter(pk=same_day.pk).update(is_active=False)
        assert same_day not in shipping_services.available_methods(gov, area)

        ShippingMethod.objects.filter(pk=same_day.pk).update(is_active=True)
        same_day.refresh_from_db()
        assert same_day in shipping_services.available_methods(gov, area)

        # Staff withdraw the area's eligibility: the method stays on, the offer
        # does not.
        ServiceArea.objects.filter(pk=area.pk).update(same_day_eligible=False)
        area.refresh_from_db()
        assert same_day not in shipping_services.available_methods(gov, area)

        # And an address that names no area at all is never same-day.
        assert same_day not in shipping_services.available_methods(gov, None)

    def test_an_ineligible_area_cannot_be_quoted_even_if_it_is_asked_for(
        self, destination, site_setting
    ):
        """FR-047: the eligibility gate is enforced at quote time, not only in the list.

        Hiding a method from the list is presentation. A posted request naming
        it directly must be refused too, or the gate is decorative.
        """
        gov, area = destination
        same_day = ShippingMethod.objects.create(
            code="same-day-fr047-quote",
            label="توصيل في نفس اليوم",
            position=1,
            is_active=True,
            requires_area_eligibility=True,
        )
        make_rate(same_day, gov)
        ServiceArea.objects.filter(pk=area.pk).update(same_day_eligible=False)
        area.refresh_from_db()

        with pytest.raises(ValidationError):
            shipping_services.quote_shipping(same_day, gov, area, Decimal("100.00"))
        with pytest.raises(ValidationError):
            shipping_services.quote_shipping(same_day, gov, None, Decimal("100.00"))


# ---------------------------------------------------------------------------
# Installation eligibility (FR-048)
# ---------------------------------------------------------------------------


class TestInstallationEligibility:
    def test_installation_needs_an_eligible_governorate_and_installable_lines(
        self, destination, product, variant, stock
    ):
        """FR-048: both conditions, and each one alone is enough to withdraw it.

        The cart is grown line by line: one installable product in an eligible
        governorate is offered installation; the same cart in a governorate the
        service does not cover is not; and adding a single line that does not
        support installation withdraws the offer for the whole cart, because
        installation is a visit, not a per-line extra.
        """
        from apps.cart.services import add_to_cart, get_or_create_cart
        from apps.catalog.models import Product, ProductVariant
        from apps.core.models import PublicationStatus
        from apps.inventory.models import StockItem

        gov, _ = destination
        service = InstallationService.objects.create(
            # Development placeholder: the real fee is T-2006 business input.
            fee=Decimal("11.00"),
            is_active=True,
            is_placeholder=True,
        )
        service.governorates.add(gov)

        product.installation_supported = True
        product.save(update_fields=["installation_supported"])

        basket = get_or_create_cart(session_key="fr048-session")
        add_to_cart(basket, variant, 1)

        assert shipping_services.installation_available(gov, basket) is True

        # Same cart, a governorate the service does not cover.
        uncovered = Governorate.objects.create(key="fr048-uncovered", name="محافظة غير مغطاة")
        assert shipping_services.installation_available(uncovered, basket) is False

        # One line that does not support installation withdraws the offer.
        no_install = Product.objects.create(
            slug="fr048-no-install",
            name="منتج بدون تركيب",
            category=product.category,
            status=PublicationStatus.PUBLISHED,
            installation_supported=False,
        )
        other = ProductVariant.objects.create(
            product=no_install,
            sku="FR048-NO-INSTALL",
            finish_id="default",
            finish_label="",
            price=Decimal("100.00"),
            is_default=True,
        )
        StockItem.objects.create(variant=other, on_hand=5, reserved=0)
        add_to_cart(basket, other, 1)

        assert basket.lines.count() == 2
        assert shipping_services.installation_available(gov, basket) is False
        assert shipping_services.quote_installation(gov, basket) is None

    def test_an_empty_cart_is_not_offered_installation(self, destination, product):
        """FR-048: "every line supports installation" is not vacuously true.

        An empty cart has no line that fails the test, so a naive ``all()``
        would offer installation for nothing at all.
        """
        from apps.cart.services import get_or_create_cart

        gov, _ = destination
        service = InstallationService.objects.create(
            fee=Decimal("11.00"), is_active=True, is_placeholder=True
        )
        service.governorates.add(gov)

        empty = get_or_create_cart(session_key="fr048-empty-session")

        assert shipping_services.installation_available(gov, empty) is False


# ---------------------------------------------------------------------------
# Free shipping threshold (FR-046)
# ---------------------------------------------------------------------------


class TestFreeShippingThreshold:
    def test_the_threshold_is_configuration_rather_than_a_constant(
        self, destination, site_setting
    ):
        """FR-046: one basket, two thresholds, two different answers.

        Nothing about the cart changes between the two quotes — only the
        configured threshold — so the flip from charged to free can have no
        other cause. The boundary is inclusive: exactly at the threshold ships
        free.
        """
        gov, area = destination
        method = ShippingMethod.objects.create(
            code="fr046-standard",
            label="شحن قياسي",
            position=0,
            is_active=True,
            free_over_threshold=True,
        )
        # Deliberately fake development price (T-2006 is still open).
        make_rate(method, gov, price="11.00", placeholder=True)
        basket = Decimal("500.00")

        site_setting.free_shipping_threshold = Decimal("600.00")
        site_setting.save(update_fields=["free_shipping_threshold"])
        charged = shipping_services.quote_shipping(method, gov, area, basket)
        assert charged.free_applied is False
        assert charged.amount == Decimal("11.00")

        site_setting.free_shipping_threshold = Decimal("500.00")
        site_setting.save(update_fields=["free_shipping_threshold"])
        at_the_line = shipping_services.quote_shipping(method, gov, area, basket)
        assert at_the_line.free_applied is True, "the threshold must be inclusive"
        assert at_the_line.amount == Decimal("0.00")

        site_setting.free_shipping_threshold = Decimal("400.00")
        site_setting.save(update_fields=["free_shipping_threshold"])
        free = shipping_services.quote_shipping(method, gov, area, basket)
        assert free.free_applied is True
        assert free.amount == Decimal("0.00")

    def test_the_threshold_is_measured_against_the_discounted_subtotal(
        self, destination, site_setting, variant, stock
    ):
        """FR-046: a discount that drops the basket under the threshold restores the charge.

        The gross subtotal clears the threshold on its own here, so the only
        thing that can make the cart fail to qualify is the discount being
        subtracted first.
        """
        from apps.cart.services import add_to_cart, get_or_create_cart, price_cart
        from apps.promotions.models import Coupon, DiscountType

        gov, area = destination
        method = ShippingMethod.objects.create(
            code="fr046-discounted",
            label="شحن قياسي",
            position=0,
            is_active=True,
            free_over_threshold=True,
        )
        make_rate(method, gov, price="11.00", placeholder=True)

        basket = get_or_create_cart(session_key="fr046-session")
        add_to_cart(basket, variant, 1)
        gross = variant.price

        # A threshold the gross subtotal clears comfortably…
        site_setting.free_shipping_threshold = (gross * Decimal("0.75")).quantize(
            Decimal("0.01")
        )
        site_setting.save(update_fields=["free_shipping_threshold"])

        undiscounted = price_cart(basket)
        assert undiscounted.subtotal >= site_setting.free_shipping_threshold
        assert undiscounted.free_shipping_qualified is True

        # …and a coupon that takes it back under.
        coupon = Coupon.objects.create(
            code="FR046HALF",
            discount_type=DiscountType.PERCENTAGE,
            value=Decimal("50.00"),
            is_demo=True,
        )
        discounted_totals = price_cart(basket, coupon=coupon)
        assert discounted_totals.subtotal >= site_setting.free_shipping_threshold
        assert discounted_totals.discount_total > Decimal("0.00")
        assert discounted_totals.free_shipping_qualified is False
        assert discounted_totals.remaining_for_free_shipping > Decimal("0.00")

        discounted = discounted_totals.subtotal - discounted_totals.discount_total
        quote = shipping_services.quote_shipping(method, gov, area, discounted)
        assert quote.free_applied is False
        assert quote.amount == Decimal("11.00")
