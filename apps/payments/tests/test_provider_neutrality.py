"""The payment provider boundary, and the absence behind it (T-1101, T-1103).

Two different kinds of claim are defended here, and they need different kinds of
evidence.

The first is architectural: payments are modelled as four collaborating tables
plus one abstract gateway, so that connecting a provider later touches the
boundary and nothing else. That is asserted against the models and the gateway
module directly.

The second is an **absence**, and an absence can only be proved by looking
everywhere. ``tests/security/test_no_card_data.py`` sets the pattern this file
follows: scan the shipped source and assert the thing is not there. No payment
SDK is imported, no package is installed, no gateway endpoint appears, no
credential is configured. "There is no provider integration" is therefore a
checked fact about the repository rather than a sentence in a docstring — and it
stays checked, because the day somebody adds one, this file fails.
"""

from __future__ import annotations

import ast
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ValidationError

from apps.payments import gateways
from apps.payments.models import (
    Payment,
    PaymentEvent,
    PaymentMethod,
    Refund,
)

pytestmark = pytest.mark.django_db

#: Everything that ships. Test files are excluded: this module names providers
#: precisely in order to assert they are absent, and must not trip its own scan.
SCANNED_ROOTS = ("apps", "storefront", "config", "scripts", "templates", "static/src", "deploy")

SCANNED_SUFFIXES = {".py", ".html", ".js", ".json", ".sh", ".conf", ".service"}

#: Import names of the payment SDKs a shop like this would plausibly reach for.
#: Matched as *import statements*, never as prose: "instapay" and
#: "vodafone-cash" are display labels the storefront legitimately renders, and a
#: word-matching scan would flag them and prove nothing.
PROVIDER_SDKS = (
    "stripe",
    "paymob",
    "paytabs",
    "fawry",
    "adyen",
    "braintree",
    "razorpay",
    "moyasar",
    "myfatoorah",
    "kashier",
    "geidea",
    "payfort",
    "hyperpay",
    "checkout_sdk",
    "paypalrestsdk",
    "paypalhttp",
    "squareup",
    "telr",
    "opay",
    "tap_payments",
    "amazon_payment_services",
    "xpay",
)

#: Hosts a live integration would have to talk to. Full host names, so a match
#: is a real endpoint and not a coincidence.
PROVIDER_ENDPOINTS = (
    "api.stripe.com",
    "accept.paymob.com",
    "paymob.com",
    "atfawry.com",
    "secure.paytabs.com",
    "paytabs.com",
    "checkout.adyen.com",
    "api.razorpay.com",
    "api.moyasar.com",
    "api.tap.company",
    "oppwa.com",
    "payfort.com",
    "api.kashier.io",
    "geidea.net",
    "api.paypal.com",
    "connect.squareup.com",
    "api.myfatoorah.com",
)

#: Credential names a provider integration would need before it could run.
CREDENTIAL_PREFIXES = (
    "STRIPE_",
    "PAYMOB_",
    "PAYTABS_",
    "FAWRY_",
    "ADYEN_",
    "RAZORPAY_",
    "MOYASAR_",
    "MYFATOORAH_",
    "KASHIER_",
    "GEIDEA_",
    "PAYFORT_",
    "HYPERPAY_",
    "PAYPAL_",
    "SQUARE_",
)


def shipped_files(suffixes=(".py",)):
    """Every source file that ships, excluding the test tree."""
    wanted = set(suffixes)
    for root in SCANNED_ROOTS:
        base = Path(settings.BASE_DIR, root)
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in wanted:
                continue
            parts = set(path.parts)
            if "__pycache__" in parts or "tests" in parts or path.name.startswith("test_"):
                continue
            yield path


def imported_modules(path: Path) -> set[str]:
    """Top-level module names ``path`` imports, read from its AST.

    An AST walk rather than a regex: it sees ``import x.y as z`` and ignores the
    same words appearing in a comment or a string.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:  # pragma: no cover - a syntax error is another test's job
        return set()
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module.split(".")[0])
    return names


@pytest.fixture
def order(db):
    from apps.orders.models import Order

    return Order.objects.create(
        number="ZK-NEUTRAL-0001",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="neutral-0001",
        subtotal=Decimal("500.00"),
        grand_total=Decimal("500.00"),
    )


@pytest.fixture
def cod(db):
    return PaymentMethod.objects.create(
        code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True
    )


# ---------------------------------------------------------------------------
# The architecture is provider-neutral
# ---------------------------------------------------------------------------


class TestTheArchitectureIsProviderNeutral:
    def test_the_four_declared_tables_exist_and_stay_separate(self):
        """FR-070: configuration, attempt, event log and refund are four things.

        Collapsing any pair — method config onto the attempt, the event log onto
        the payment — is what turns "swap the provider" into a schema migration,
        so the separation is asserted rather than assumed.
        """
        assert Payment._meta.get_field("method").related_model is PaymentMethod
        assert PaymentEvent._meta.get_field("payment").related_model is Payment
        assert Refund._meta.get_field("payment").related_model is Payment
        assert Payment._meta.get_field("order").related_model.__name__ == "Order"

        # Configuration knows nothing about an order or an attempt: it is the
        # method itself, reusable across every payment made with it.
        config_fields = {f.name for f in PaymentMethod._meta.get_fields()}
        assert "order" not in config_fields
        assert "amount" not in config_fields

    def test_the_event_log_can_only_be_appended_to(self, order, cod):
        """FR-070: PaymentEvent is written once and never rewritten or removed."""
        payment = Payment.objects.create(
            order=order, method=cod, amount=Decimal("500.00"), currency="EGP"
        )
        event = PaymentEvent.objects.create(payment=payment, event_type="created")

        event.note = "أعيدت كتابته"
        with pytest.raises(ValidationError):
            event.save()
        with pytest.raises(ValidationError):
            event.delete()

        stored = PaymentEvent.objects.get(pk=event.pk)
        assert stored.note == "", "an append-only event was rewritten"

    def test_no_column_is_named_after_a_particular_provider(self):
        """FR-070: the provider-facing columns are generic, so any provider fits."""
        offenders = []
        for model in (PaymentMethod, Payment, PaymentEvent, Refund):
            for field in model._meta.get_fields():
                name = getattr(field, "name", "").lower()
                offenders += [
                    f"{model.__name__}.{name}" for sdk in PROVIDER_SDKS if sdk in name
                ]
        assert offenders == [], f"provider-specific columns: {offenders}"

        assert "provider_reference" in {f.name for f in Payment._meta.fields}
        assert "provider_event_id" in {f.name for f in PaymentEvent._meta.fields}

    def test_a_gateway_cannot_write_a_row_itself(self):
        """FR-070: deciding whether money moved stays in the service layer.

        A gateway that wrote its own ``Payment`` would put provider-specific code
        on the money path, which is the exact coupling provider-neutrality is
        there to prevent — so the boundary module must contain no writes at all.
        """
        source = Path(gateways.__file__).read_text(encoding="utf-8")
        for forbidden in (
            "Payment.objects",
            "Refund.objects",
            "PaymentEvent.objects",
            ".save(",
            ".create(",
            ".update(",
        ):
            assert forbidden not in source, f"gateways.py writes rows itself: {forbidden}"


# ---------------------------------------------------------------------------
# No provider integration exists anywhere in the repository
# ---------------------------------------------------------------------------


class TestNoProviderIntegrationExists:
    def test_no_payment_provider_sdk_is_imported_anywhere(self):
        """FR-071: not one line of shipped code imports a gateway SDK."""
        offenders = []
        for path in shipped_files():
            for name in sorted(imported_modules(path) & set(PROVIDER_SDKS)):
                offenders.append(f"{path.relative_to(settings.BASE_DIR)}: {name}")
        assert offenders == [], f"payment provider SDKs are imported: {offenders}"

    def test_no_payment_provider_package_is_installed(self):
        """FR-071: nothing *could* be imported, because nothing is declared."""
        pyproject = (
            Path(settings.BASE_DIR, "pyproject.toml").read_text(encoding="utf-8").lower()
        )
        declared = [
            sdk
            for sdk in PROVIDER_SDKS
            if sdk in pyproject or sdk.replace("_", "-") in pyproject
        ]
        assert declared == [], f"pyproject declares provider packages: {declared}"

    def test_no_live_gateway_endpoint_appears_in_the_source(self):
        """FR-071: there is nowhere for a payment request to be sent."""
        offenders = []
        candidates = list(shipped_files(SCANNED_SUFFIXES))
        candidates.append(Path(settings.BASE_DIR, ".env.example"))
        for path in candidates:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for host in PROVIDER_ENDPOINTS:
                if host in text:
                    offenders.append(f"{path.relative_to(settings.BASE_DIR)}: {host}")
        assert offenders == [], f"live gateway endpoints present: {offenders}"

    def test_no_provider_credential_is_configured(self):
        """FR-071: a live integration needs a secret, and none is declared.

        Settings and the environment template are the only two places a
        credential name could legitimately appear.
        """
        offenders = []
        candidates = [
            *Path(settings.BASE_DIR, "config").rglob("*.py"),
            Path(settings.BASE_DIR, ".env.example"),
        ]
        for path in candidates:
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for prefix in CREDENTIAL_PREFIXES:
                if prefix in text:
                    offenders.append(f"{path.relative_to(settings.BASE_DIR)}: {prefix}")
        assert offenders == [], f"provider credentials are configured: {offenders}"

    def test_the_only_gateways_that_exist_settle_offline(self):
        """FR-071: the shipped gateways are cash on delivery and manual, only."""
        classes = {
            obj.__name__: obj
            for obj in vars(gateways).values()
            if isinstance(obj, type)
            and issubclass(obj, gateways.PaymentGateway)
            and obj is not gateways.PaymentGateway
        }
        assert set(classes) == {"CODGateway", "ManualGateway"}
        for name, cls in classes.items():
            assert cls().is_external is False, f"{name} reaches a remote provider"

    def test_every_configured_method_resolves_to_an_offline_gateway(
        self, seeded_catalogue
    ):
        """FR-071: every method the shop offers is COD or manual; the rest are refused."""
        methods = list(PaymentMethod.objects.all())
        assert methods, "no payment methods are configured at all"
        assert not [m.code for m in methods if m.is_integrated], (
            "a configured method claims a provider integration"
        )

        for method in methods:
            if method.is_available_for_checkout:
                assert isinstance(
                    gateways.gateway_for(method),
                    (gateways.CODGateway, gateways.ManualGateway),
                ), f"{method.code} is offered but is neither COD nor manual"
            else:
                with pytest.raises(ValidationError):
                    gateways.gateway_for(method)


# ---------------------------------------------------------------------------
# A real integration remains a separate, gated task
# ---------------------------------------------------------------------------


class TestProviderIntegrationRemainsASeparateTask:
    def test_no_integration_has_been_started_under_another_name(self):
        """FR-079: the increment is still separable because it is still untouched.

        "Separately identifiable" stops being true the moment half an
        integration is smuggled into the current scope — a client module here, a
        credential there. The scan is the same one FR-071 uses; the claim it
        supports here is that the *task* has not begun.
        """
        started = []
        for path in shipped_files():
            started += [
                f"{path.relative_to(settings.BASE_DIR)}: {name}"
                for name in sorted(imported_modules(path) & set(PROVIDER_SDKS))
            ]
        assert started == [], f"provider integration work has already begun: {started}"

        # The one switch that could pretend otherwise refuses to work.
        pretend = PaymentMethod.objects.create(
            code="payment-card", label="بطاقة", is_integrated=True
        )
        with pytest.raises(ValidationError, match="لا يوجد تكامل"):
            gateways.gateway_for(pretend)

    def test_the_task_is_gated_on_credentials_documentation_and_test_mode(self):
        """FR-079: the three preconditions are written down, not remembered.

        The requirement is about *when* an integration may start, so the gate
        itself is the artifact. Deleting it, or quietly dropping one of the three
        prerequisites, would let the work begin without them — and fails here.
        """
        gate_document = Path(
            settings.BASE_DIR,
            "specs",
            "004-zakey-commerce-backend-admin",
            "payment-state-machine.md",
        )
        lines = [
            line.lower()
            for line in gate_document.read_text(encoding="utf-8").splitlines()
            if "real provider task may only start when" in line.lower()
        ]
        assert lines, "the provider-integration gate is no longer documented"

        gate = lines[0]
        for prerequisite in ("credentials", "documentation", "test mode"):
            assert prerequisite in gate, f"the gate no longer requires {prerequisite}"
