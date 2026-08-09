"""No card data anywhere (T-1108, FR-077, FR-078).

`tasks.md` names this file as T-1108's evidence and it did not exist. The claim
it must defend is absolute: **card numbers, CVV and full PAN are never stored,
logged, or transmitted to this system.**

That claim is defended structurally rather than procedurally. The strongest
guarantee is not "we are careful with card fields" — it is that there is nowhere
to put one: no model field accepts a PAN, no gateway is connected, and the log
redactor destroys anything card-shaped that reaches it anyway.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.apps import apps as django_apps
from django.conf import settings

pytestmark = pytest.mark.django_db

#: Field names that would indicate somewhere to store card data.
CARD_FIELD_HINTS = (
    "card_number",
    "cardnumber",
    "pan",
    "cvv",
    "cvc",
    "security_code",
    "card_expiry",
    "expiry_month",
    "expiry_year",
    "cardholder",
)

#: Test PANs from the major schemes; all pass a Luhn check.
SAMPLE_PANS = [
    "4111111111111111",  # Visa
    "5500005555555559",  # Mastercard
    "340000000000009",  # Amex
    "6011000000000004",  # Discover
]


class TestNoModelCanStoreCardData:
    def test_no_field_name_suggests_card_storage(self):
        offenders = []
        for model in django_apps.get_models():
            for field in model._meta.get_fields():
                name = getattr(field, "name", "").lower()
                if any(hint in name for hint in CARD_FIELD_HINTS):
                    offenders.append(f"{model._meta.label}.{name}")
        assert offenders == [], f"fields that could hold card data: {offenders}"

    def test_the_payment_model_stores_no_card_columns(self):
        from apps.payments.models import Payment

        names = {f.name.lower() for f in Payment._meta.get_fields()}
        assert not (names & set(CARD_FIELD_HINTS))

    def test_no_payment_method_claims_a_live_integration(self):
        """FR-072: no provider is connected, so no PAN can reach one."""
        from apps.payments.models import PaymentMethod

        integrated = [m.code for m in PaymentMethod.objects.filter(is_integrated=True)]
        assert integrated == [], f"a payment method claims live integration: {integrated}"


class TestCardNumbersAreRedactedFromLogs:
    @pytest.mark.parametrize("pan", SAMPLE_PANS)
    def test_a_pan_never_survives_redaction(self, pan):
        from apps.core.logging import redact

        assert pan not in redact(f"charging card {pan} for order ZK-1")

    @pytest.mark.parametrize("pan", SAMPLE_PANS)
    def test_a_spaced_pan_is_also_redacted(self, pan):
        """Card numbers are commonly written in groups of four."""
        from apps.core.logging import redact

        grouped = " ".join(pan[i : i + 4] for i in range(0, len(pan), 4))
        result = redact(f"card {grouped}")
        assert not re.search(r"\b\d{13,19}\b", result.replace(" ", ""))

    def test_a_cvv_assignment_is_redacted(self):
        from apps.core.logging import redact

        assert "123" not in redact("cvv=123")

    def test_the_redactor_runs_on_every_configured_handler(self):
        for name, handler in settings.LOGGING["handlers"].items():
            assert "redact" in handler.get("filters", []), (
                f"handler {name!r} would log a PAN verbatim"
            )

    def test_a_real_log_record_carrying_a_pan_is_scrubbed(self, caplog):
        import logging

        from apps.core.logging import RedactingFilter

        logger = logging.getLogger("zakey.test.pan")
        logger.addFilter(RedactingFilter())

        with caplog.at_level(logging.INFO, logger="zakey.test.pan"):
            logger.info("payment attempt with 4111111111111111")

        emitted = "".join(record.getMessage() for record in caplog.records)
        assert "4111111111111111" not in emitted


class TestNoCardDataInTheCodebase:
    def test_no_template_asks_for_a_card_number(self):
        """A field that does not exist cannot be submitted."""
        offenders = []
        for template in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            text = template.read_text(encoding="utf-8").lower()
            for hint in ("card_number", "cardnumber", "cvv", "cvc", "autocomplete=\"cc-"):
                if hint in text:
                    offenders.append(f"{template.name}: {hint}")
        assert offenders == [], f"templates collect card data: {offenders}"

    def test_no_form_declares_a_card_field(self):
        """Word-boundary matched: ``pan`` also appears inside ``company``."""
        offenders = []
        hint_re = re.compile(
            r"\b(" + "|".join(re.escape(h) for h in CARD_FIELD_HINTS) + r")\b"
        )
        for module in Path(settings.BASE_DIR).rglob("*forms*.py"):
            if "/.venv/" in str(module):
                continue
            found = hint_re.findall(
                module.read_text(encoding="utf-8", errors="ignore").lower()
            )
            offenders += [f"{module.name}: {hint}" for hint in sorted(set(found))]
        assert offenders == [], f"forms accept card data: {offenders}"

    def test_no_production_source_contains_a_literal_pan(self):
        """A PAN in *production* source is a PAN in the repository.

        Test files are excluded deliberately, and the exclusion is narrow: a
        test may name a PAN in order to prove the system destroys it — which is
        exactly what ``test_only_a_digest_of_the_payload_is_stored`` does. What
        must never happen is a card number reaching shipped code.
        """
        offenders = []
        pattern = re.compile(r"\b(?:4\d{15}|5[1-5]\d{14}|3[47]\d{13}|6011\d{12})\b")
        for root in ("apps", "storefront", "config", "templates", "static/src"):
            base = Path(settings.BASE_DIR, root)
            if not base.exists():
                continue
            for path in base.rglob("*"):
                if not path.is_file() or path.suffix not in {".py", ".html", ".js", ".json"}:
                    continue
                parts = set(path.parts)
                if "__pycache__" in parts or "tests" in parts or path.name.startswith("test_"):
                    continue
                if pattern.search(path.read_text(encoding="utf-8", errors="ignore")):
                    offenders.append(str(path.relative_to(settings.BASE_DIR)))
        assert offenders == [], f"card numbers present in production source: {offenders}"

    def test_a_provider_payload_is_stored_only_as_a_digest(self, db):
        """The protection the exclusion above relies on, asserted here directly."""
        from apps.payments.models import PaymentEvent

        fields = {f.name for f in PaymentEvent._meta.fields}
        assert "payload_digest" in fields
        assert "payload" not in fields, (
            "PaymentEvent stores a raw provider payload, which could carry a PAN"
        )


class TestPaymentRecordsCarryNoCardData:
    def test_a_recorded_payment_stores_only_a_reference(self, db):
        """What a payment keeps is a provider reference, never an instrument."""
        from decimal import Decimal

        from apps.orders.models import Order
        from apps.payments.models import Payment, PaymentMethod

        order = Order.objects.create(
            number="ZK-PAN-1",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="key-pan-1",
            subtotal=Decimal("100.00"),
            grand_total=Decimal("100.00"),
        )
        method = PaymentMethod.objects.create(code="cod", label="عند الاستلام")
        payment = Payment.objects.create(
            order=order, method=method, amount=Decimal("100.00"), currency="EGP"
        )

        serialised = " ".join(
            str(getattr(payment, f.name, "")) for f in Payment._meta.fields
        )
        assert not re.search(r"\b\d{13,19}\b", serialised), (
            "a payment row holds a card-length number"
        )
