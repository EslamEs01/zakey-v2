"""The approved commercial launch policy (T-2006, ASM-004, ASM-005).

The business decision is a **disabled-service launch**, and the distinction that
matters is between that and the state it superficially resembles:

* *disabled service* — shipping is free at or above EGP 1,500, nothing paid is
  offered below it, installation is switched off. Every active figure is
  approved. Production must start in this state without complaint.
* *unapproved placeholder* — a development number nobody signed off, still
  switched on, about to be charged to a customer. Production must refuse.

Telling those two apart is the whole job of `apply_launch_policy`, the shipping
system checks, and these tests. A launch gate that opens because someone deleted
the check is not a gate, so the tests below assert the refusal as hard as they
assert the acceptance.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.test import override_settings

from apps.shipping import services as shipping_services
from apps.shipping.checks import (
    PLACEHOLDER_INSTALLATION,
    PLACEHOLDER_SHIPPING,
    commercial_rates_are_approved,
)
from apps.shipping.models import (
    Governorate,
    InstallationService,
    ShippingMethod,
    ShippingRate,
    ShippingZone,
)

pytestmark = pytest.mark.django_db

THRESHOLD = Decimal("1500.00")

#: Enough environment for `config.settings.production` to import. Mirrors the
#: fixture in `test_deploy_check.py`; duplicated rather than shared because the
#: claim under test is about production's *defaults*, and importing it with a
#: half-populated environment would prove the wrong thing.
REQUIRED_ENV = {
    "DJANGO_SECRET_KEY": "x" * 60,
    "DJANGO_ALLOWED_HOSTS": "shop.zakey.example.eg",
    "CSRF_TRUSTED_ORIGINS": "https://shop.zakey.example.eg",
    "DATABASE_URL": "postgres://zakey@127.0.0.1:5433/zakey",
    "DEFAULT_FROM_EMAIL": "no-reply@zakey.example.eg",
}


@pytest.fixture(scope="module")
def production_settings():
    """Import `config.settings.production` with plausible env values."""
    import importlib
    import os

    previous = {key: os.environ.get(key) for key in REQUIRED_ENV}
    os.environ.update(REQUIRED_ENV)
    try:
        module = importlib.import_module("config.settings.production")
        yield importlib.reload(module)
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@pytest.fixture
def launch_state(db, site_setting, governorate):
    """The approved launch configuration, built the way a deploy builds it."""
    site_setting.free_shipping_threshold = THRESHOLD
    site_setting.save(update_fields=["free_shipping_threshold"])

    zone = ShippingZone.objects.create(name="كل المحافظات", position=0)
    zone.governorates.add(governorate)

    free = ShippingMethod.objects.create(
        code="shipping-free", label="شحن مجاني", position=0,
        is_active=True, free_over_threshold=True,
    )
    paid = ShippingMethod.objects.create(
        code="shipping-standard", label="شحن قياسي", position=1,
        is_active=True, free_over_threshold=False,
    )
    # Seeded as development placeholders, exactly as `seed_demo` leaves them.
    ShippingRate.objects.create(
        method=free, zone=zone, price=Decimal("0.00"), is_placeholder=True, is_active=True
    )
    ShippingRate.objects.create(
        method=paid, zone=zone, price=Decimal("75.00"), is_placeholder=True, is_active=True
    )
    service = InstallationService.objects.create(
        name="خدمة التركيب", fee=Decimal("250.00"), is_placeholder=True, is_active=True
    )
    service.governorates.add(governorate)

    call_command("apply_launch_policy", stdout=StringIO())
    return {"zone": zone, "free": free, "paid": paid, "service": service}


class TestTheLaunchGateIsClosedThenOpened:
    def test_seeded_placeholders_hold_the_gate_shut(self, db, site_setting, governorate):
        """Before the policy is applied, the launch gate reports unapproved money."""
        zone = ShippingZone.objects.create(name="كل المحافظات")
        zone.governorates.add(governorate)
        method = ShippingMethod.objects.create(code="m", label="m", free_over_threshold=True)
        ShippingRate.objects.create(method=method, zone=zone, is_placeholder=True)

        assert shipping_services.has_unapproved_rates() is True

    def test_applying_the_policy_opens_it(self, launch_state):
        """T-2006: no active placeholder rate exists once the policy is applied."""
        assert shipping_services.has_unapproved_rates() is False
        assert not ShippingRate.objects.filter(is_active=True, is_placeholder=True).exists()
        assert not InstallationService.objects.filter(is_active=True, is_placeholder=True).exists()

    def test_the_policy_is_idempotent(self, launch_state):
        """A deploy script may run it twice; the second run must change nothing."""
        before = list(
            ShippingRate.objects.order_by("pk").values_list(
                "pk", "price", "is_active", "is_placeholder", "free_threshold_only"
            )
        )
        out = StringIO()
        call_command("apply_launch_policy", stdout=out)

        after = list(
            ShippingRate.objects.order_by("pk").values_list(
                "pk", "price", "is_active", "is_placeholder", "free_threshold_only"
            )
        )
        assert after == before
        assert "already applied" in out.getvalue()

    def test_applying_the_policy_is_auditable(self, db, site_setting, governorate):
        """T-2006: who changed the commercial configuration, and to what."""
        from apps.audit.models import AuditLog

        zone = ShippingZone.objects.create(name="كل المحافظات")
        zone.governorates.add(governorate)
        method = ShippingMethod.objects.create(code="m", label="m", free_over_threshold=True)
        ShippingRate.objects.create(method=method, zone=zone, is_placeholder=True)

        call_command("apply_launch_policy", stdout=StringIO())

        entry = AuditLog.objects.order_by("-id").first()
        assert entry is not None
        assert entry.changes["commercial_policy"] == "launch"
        assert entry.changes["paid_shipping"] == "withdrawn"
        assert entry.changes["installation"] == "disabled"
        assert entry.changes["free_shipping_threshold"] == str(THRESHOLD)


class TestQuotingUnderTheLaunchPolicy:
    def test_an_order_at_the_threshold_ships_free(self, launch_state, governorate):
        """T-2006: eligible orders get the approved rate — zero."""
        quote = shipping_services.quote_shipping(
            launch_state["free"], governorate, None, THRESHOLD
        )

        assert quote.free_applied is True
        assert quote.amount == Decimal("0.00")
        assert quote.is_placeholder is False

    def test_an_order_above_the_threshold_ships_free(self, launch_state, governorate):
        quote = shipping_services.quote_shipping(
            launch_state["free"], governorate, None, Decimal("2500.00")
        )

        assert quote.free_applied is True
        assert quote.amount == Decimal("0.00")

    def test_an_order_below_the_threshold_is_refused_not_invented(
        self, launch_state, governorate
    ):
        """T-2006: no paid shipping exists at launch, so the answer is 'no'.

        The dangerous alternative is quoting the rate's stored price — which the
        constraint pins to zero — and silently shipping a 200 EGP basket for
        nothing.
        """
        with pytest.raises(shipping_services.FulfillmentUnavailable) as raised:
            shipping_services.quote_shipping(
                launch_state["free"], governorate, None, Decimal("200.00")
            )

        message = str(raised.value)
        assert "غير متاح" in message
        assert "1500" in message, "the refusal should say what would qualify"

    def test_a_below_threshold_basket_is_offered_no_method_at_all(
        self, launch_state, governorate
    ):
        """T-2006: unavailable options are not listed as choosable."""
        offered = shipping_services.available_methods(
            governorate, None, Decimal("200.00")
        )

        assert offered == []

    def test_an_eligible_basket_is_offered_the_free_method(self, launch_state, governorate):
        offered = shipping_services.available_methods(governorate, None, THRESHOLD)

        assert [m.code for m in offered] == ["shipping-free"]

    def test_the_withdrawn_paid_method_is_never_offered(self, launch_state, governorate):
        """Even a rich basket must not be shown a method whose rate is withdrawn."""
        offered = shipping_services.available_methods(
            governorate, None, Decimal("9999.00")
        )

        assert "shipping-standard" not in [m.code for m in offered]

    def test_the_withdrawn_paid_method_cannot_be_quoted_by_forcing_it(
        self, launch_state, governorate
    ):
        """Hiding it from the list is presentation; the refusal must be real."""
        with pytest.raises(shipping_services.FulfillmentUnavailable):
            shipping_services.quote_shipping(
                launch_state["paid"], governorate, None, Decimal("9999.00")
            )


class TestInstallationIsOff:
    def test_installation_is_not_available_anywhere(self, launch_state, governorate):
        assert shipping_services.installation_available(governorate, None) is False
        assert shipping_services.quote_installation(governorate, None) is None

    def test_the_storefront_does_not_offer_it(self, launch_state):
        """T-2006: not displayed, so not selectable."""
        from storefront import context as ctx

        assert ctx.installation_offered() is False

    def test_it_is_offered_again_only_when_deliberately_configured(
        self, launch_state, governorate
    ):
        """Re-enabling is an explicit act with an approved figure, not a default."""
        from storefront import context as ctx

        service = launch_state["service"]
        service.is_active = True
        service.fee = Decimal("300.00")
        service.is_placeholder = False
        service.save(update_fields=["is_active", "fee", "is_placeholder"])

        # Still not offered: activating the service is not enough without coverage.
        assert ctx.installation_offered() is False

        service.governorates.add(governorate)
        assert ctx.installation_offered() is True


class TestProductionStartupAcceptsTheLaunchState:
    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_the_approved_disabled_service_state_passes(self, launch_state):
        """T-2006: an intentional disabled-service launch is not an error."""
        assert commercial_rates_are_approved(None) == []

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_an_active_placeholder_rate_fails_startup(self, launch_state):
        ShippingRate.objects.filter(is_active=True).update(is_placeholder=True)

        errors = commercial_rates_are_approved(None)

        assert [e.id for e in errors] == [PLACEHOLDER_SHIPPING]

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False)
    def test_an_active_placeholder_installation_fee_fails_startup(
        self, launch_state, governorate
    ):
        InstallationService.objects.update(is_active=True, is_placeholder=True)

        errors = commercial_rates_are_approved(None)

        assert PLACEHOLDER_INSTALLATION in [e.id for e in errors]

    @override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=True)
    def test_development_may_run_on_placeholders(self, launch_state):
        """The flag exists so development is usable; production defaults it off."""
        ShippingRate.objects.filter(is_active=True).update(is_placeholder=True)

        assert commercial_rates_are_approved(None) == []

    def test_production_settings_default_the_flag_off(self, production_settings):
        """Configuration must not leak from development into production.

        Development and test both switch placeholders on so the shop is usable
        before the business has priced anything. Production reads the same name
        from the environment and defaults it **off**, so forgetting to set it
        fails closed.
        """
        assert production_settings.ZAKEY_ALLOW_PLACEHOLDER_RATES is False

    def test_the_check_survives_an_unmigrated_database(self, monkeypatch):
        """`manage.py check` legitimately runs before `migrate` on a fresh host.

        A check that raises there would block the very command that fixes it, so
        the database error is swallowed and the check reports nothing. Simulated
        by making the query raise rather than by dropping the table, which would
        abort the surrounding test transaction.
        """
        from django.db import DatabaseError

        class Exploding:
            def filter(self, *args, **kwargs):
                raise DatabaseError('relation "shipping_shippingrate" does not exist')

        monkeypatch.setattr(ShippingRate, "objects", Exploding(), raising=False)

        with override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False):
            assert commercial_rates_are_approved(None) == []


class TestTheSafeguardsThatMustNotBeWeakened:
    def test_a_placeholder_quote_is_still_refused_in_production(
        self, launch_state, governorate
    ):
        """The pre-existing guard stays: production never quotes unapproved money."""
        ShippingRate.objects.filter(method=launch_state["free"]).update(
            is_placeholder=True, free_threshold_only=False, price=Decimal("40.00")
        )

        with override_settings(ZAKEY_ALLOW_PLACEHOLDER_RATES=False):
            with pytest.raises(shipping_services.PlaceholderRateError):
                shipping_services.quote_shipping(
                    launch_state["free"], governorate, None, Decimal("100.00")
                )

    def test_a_free_threshold_rate_cannot_secretly_carry_a_price(self, launch_state):
        """The database refuses the contradiction, not just the service.

        A free-above-threshold rate with a non-zero price would reintroduce paid
        shipping below the threshold through one careless admin edit.
        """
        from django.db import IntegrityError, transaction

        rate = ShippingRate.objects.get(method=launch_state["free"])
        assert rate.free_threshold_only is True

        with pytest.raises(IntegrityError), transaction.atomic():
            ShippingRate.objects.filter(pk=rate.pk).update(price=Decimal("99.00"))

    def test_the_refusal_message_leaks_no_configuration(self, launch_state, governorate):
        """Errors carry the customer-facing threshold, never internals."""
        with pytest.raises(shipping_services.FulfillmentUnavailable) as raised:
            shipping_services.quote_shipping(
                launch_state["free"], governorate, None, Decimal("10.00")
            )

        message = str(raised.value)
        for secret in ("DATABASE_URL", "SECRET_KEY", "postgres://", "placeholder", "Traceback"):
            assert secret not in message
