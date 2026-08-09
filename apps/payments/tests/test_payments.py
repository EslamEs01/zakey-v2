"""Payments and refunds within the approved launch scope (T-1101 – T-1108).

Scope under test is deliberately narrow: cash on delivery and manual/offline
recording. There is no provider integration, and
:class:`ProviderBoundaryTests` asserts that there still isn't one.
"""

from __future__ import annotations

from decimal import Decimal
from io import StringIO

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from apps.orders.models import Order, PaymentStatus
from apps.payments import gateways, services
from apps.payments.models import (
    Payment,
    PaymentEvent,
    PaymentMethod,
    PaymentState,
    Refund,
    RefundState,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def order(db):
    return Order.objects.create(
        number="ZK-PAY-0001",
        email="nada@example.com",
        phone="01012345678",
        idempotency_key="pay-idem-0001",
        subtotal=Decimal("1000.00"),
        grand_total=Decimal("1000.00"),
    )


@pytest.fixture
def cod(db):
    return PaymentMethod.objects.create(
        code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True, position=0
    )


@pytest.fixture
def manual(db):
    return PaymentMethod.objects.create(
        code="payment-instapay", label="إنستاباي", is_manual=True, position=1
    )


def _captured(order, method, amount="1000.00", key="k1"):
    payment = services.record_payment(
        order=order, method=method, amount=Decimal(amount), idempotency_key=key
    )
    return services.capture(payment, reference="REF-1")


# ---------------------------------------------------------------------------
# T-1101 — the six approved methods, none integrated
# ---------------------------------------------------------------------------


class TestSeededMethods:
    def test_all_six_methods_are_seeded_and_none_is_integrated(self, seeded_catalogue):
        methods = PaymentMethod.objects.all()
        assert methods.count() == 6
        assert not methods.filter(is_integrated=True).exists(), (
            "a method claims a provider integration; none exists (FR-072)"
        )

    def test_only_cod_and_manual_methods_are_offered_at_checkout(self, seeded_catalogue):
        """FR-071: the launch set is cash on delivery and manual/offline only.

        Everything else is displayed as coming-soon; a method is offerable only
        because it collects on delivery or is reconciled by hand.
        """
        for method in PaymentMethod.objects.all():
            expected = method.collects_on_delivery or method.is_manual
            assert method.is_available_for_checkout is expected

    def test_disabling_one_method_leaves_the_others(self, seeded_catalogue):
        PaymentMethod.objects.filter(code="payment-cashu").update(is_active=False)
        assert PaymentMethod.objects.filter(is_active=True).count() == 5


# ---------------------------------------------------------------------------
# T-1103 — the provider boundary
# ---------------------------------------------------------------------------


class TestProviderBoundary:
    def test_cod_resolves_to_the_cod_gateway(self, cod):
        assert isinstance(gateways.gateway_for(cod), gateways.CODGateway)

    def test_manual_methods_resolve_to_the_manual_gateway(self, manual):
        assert isinstance(gateways.gateway_for(manual), gateways.ManualGateway)

    def test_no_gateway_is_external(self, cod, manual):
        for method in (cod, manual):
            assert gateways.gateway_for(method).is_external is False

    def test_a_method_claiming_integration_is_refused(self, db):
        """FR-079: an integration cannot be switched on, only built.

        ``is_integrated`` is the single edit that could make the shop behave as
        though a provider were connected. The gateway lookup refuses it, so
        connecting a real provider stays a separate, visible piece of work
        rather than a flag someone flips.
        """
        pretend = PaymentMethod.objects.create(
            code="payment-card", label="بطاقة", is_integrated=True
        )
        with pytest.raises(ValidationError, match="لا يوجد تكامل"):
            gateways.gateway_for(pretend)

    def test_a_displayed_but_unconnected_method_is_refused(self, db):
        shown = PaymentMethod.objects.create(code="payment-cashu", label="كاشيو")
        with pytest.raises(ValidationError):
            gateways.gateway_for(shown)

    def test_cod_does_not_capture_at_authorisation(self, order, cod):
        """The courier has not collected yet; the order is not paid."""
        payment = services.record_payment(
            order=order, method=cod, amount=Decimal("1000.00"), idempotency_key="k"
        )
        assert payment.state == PaymentState.PENDING
        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.UNPAID

    def test_manual_capture_requires_a_reference(self, order, manual):
        payment = services.record_payment(
            order=order, method=manual, amount=Decimal("1000.00"), idempotency_key="k"
        )
        with pytest.raises(ValidationError, match="مرجع التحويل"):
            services.capture(payment, reference="")


# ---------------------------------------------------------------------------
# T-1102/T-1105 — attempts, states and derived order status
# ---------------------------------------------------------------------------


class TestPaymentLifecycle:
    def test_capture_marks_the_order_paid(self, order, cod):
        _captured(order, cod)
        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.PAID

    def test_partial_capture_marks_the_order_partially_paid(self, order, cod):
        payment = services.record_payment(
            order=order, method=cod, amount=Decimal("400.00"), idempotency_key="k"
        )
        services.capture(payment, reference="R")
        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.PARTIALLY_PAID

    def test_payment_cannot_exceed_the_order_total(self, order, cod):
        with pytest.raises(ValidationError, match="يتجاوز المتبقي"):
            services.record_payment(
                order=order, method=cod, amount=Decimal("1000.01"), idempotency_key="k"
            )

    def test_two_payments_cannot_together_exceed_the_total(self, order, cod):
        _captured(order, cod, "600.00", "k1")
        with pytest.raises(ValidationError, match="يتجاوز المتبقي"):
            services.record_payment(
                order=order, method=cod, amount=Decimal("500.00"), idempotency_key="k2"
            )

    def test_zero_and_negative_amounts_are_refused(self, order, cod):
        for amount in ("0.00", "-5.00"):
            with pytest.raises(ValidationError):
                services.record_payment(
                    order=order, method=cod, amount=Decimal(amount), idempotency_key=amount
                )

    def test_replaying_a_payment_key_returns_the_same_attempt(self, order, cod):
        first = services.record_payment(
            order=order, method=cod, amount=Decimal("100.00"), idempotency_key="same"
        )
        for _ in range(5):
            again = services.record_payment(
                order=order, method=cod, amount=Decimal("100.00"), idempotency_key="same"
            )
            assert again.pk == first.pk
        assert Payment.objects.count() == 1

    def test_captured_payment_cannot_be_failed(self, order, cod):
        payment = _captured(order, cod)
        with pytest.raises(services.InvalidPaymentTransition):
            services.mark_failed(payment, reason="لا")

    def test_failed_payment_is_terminal(self, order, cod):
        payment = services.record_payment(
            order=order, method=cod, amount=Decimal("100.00"), idempotency_key="k"
        )
        services.mark_failed(payment, reason="رفض العميل الاستلام")
        payment.refresh_from_db()
        with pytest.raises(services.InvalidPaymentTransition):
            services.capture(payment)

    def test_cancelled_payment_is_terminal(self, order, cod):
        payment = services.record_payment(
            order=order, method=cod, amount=Decimal("100.00"), idempotency_key="k"
        )
        services.cancel(payment, reason="ألغى العميل")
        payment.refresh_from_db()
        with pytest.raises(services.InvalidPaymentTransition):
            services.capture(payment)

    def test_currency_is_recorded(self, order, cod):
        payment = services.record_payment(
            order=order, method=cod, amount=Decimal("100.00"), idempotency_key="k"
        )
        assert payment.currency == "EGP"

    def test_a_payment_records_amount_currency_method_and_provider_reference(
        self, order, manual
    ):
        """FR-073: one attempt persists all five facts the requirement names.

        Read back from the database rather than from the returned instance, so
        the assertion is about the row and not about what the service happened
        to leave in memory.
        """
        payment = services.record_payment(
            order=order,
            method=manual,
            amount=Decimal("250.00"),
            idempotency_key="k-fields",
            reference="TRX-9911",
        )

        stored = Payment.objects.get(pk=payment.pk)
        assert stored.amount == Decimal("250.00")
        assert stored.currency == "EGP"
        assert stored.method_id == manual.pk
        assert stored.provider_reference == "TRX-9911"
        assert stored.state == PaymentState.PENDING

    def test_the_state_vocabulary_is_exactly_the_seven_specified_states(self):
        """FR-073: the payment state set is closed, and these are its members."""
        expected = {
            "pending",
            "authorised",
            "captured",
            "failed",
            "cancelled",
            "refunded",
            "partially_refunded",
        }
        assert set(PaymentState.values) == expected
        assert {
            value for value, _label in Payment._meta.get_field("state").choices
        } == expected

    def test_every_declared_state_can_actually_be_stored(self, order, cod):
        """FR-073: a state the column cannot hold is not a state the shop has."""
        for index, state in enumerate(PaymentState.values):
            payment = Payment.objects.create(
                order=order,
                method=cod,
                amount=Decimal("1.00"),
                currency="EGP",
                state=state,
                idempotency_key=f"state-{index}",
            )
            payment.refresh_from_db()
            assert payment.state == state

    def test_every_movement_leaves_an_immutable_event(self, order, cod):
        payment = _captured(order, cod)
        events = list(PaymentEvent.objects.filter(payment=payment))
        assert {e.event_type for e in events} == {"created", "captured"}
        with pytest.raises(ValidationError):
            events[0].delete()

    def test_capture_is_audited(self, order, cod):
        from apps.audit.models import AuditAction, AuditLog

        _captured(order, cod)
        assert AuditLog.objects.filter(action=AuditAction.PAYMENT_RECORD).exists()


# ---------------------------------------------------------------------------
# T-1104 — refunds bounded by what was captured (INV-004)
# ---------------------------------------------------------------------------


class TestRefunds:
    def test_full_refund_marks_payment_and_order_refunded(self, order, cod):
        payment = _captured(order, cod)
        services.refund(payment, Decimal("1000.00"), reason="إرجاع كامل")

        payment.refresh_from_db()
        order.refresh_from_db()
        assert payment.state == PaymentState.REFUNDED
        assert order.payment_status == PaymentStatus.REFUNDED

    def test_partial_refund_is_reflected_on_both(self, order, cod):
        payment = _captured(order, cod)
        services.refund(payment, Decimal("250.00"), reason="إرجاع جزئي")

        payment.refresh_from_db()
        order.refresh_from_db()
        assert payment.state == PaymentState.PARTIALLY_REFUNDED
        assert payment.refunded_amount == Decimal("250.00")
        assert payment.refundable_amount == Decimal("750.00")
        assert order.payment_status == PaymentStatus.PARTIALLY_REFUNDED

    def test_refunds_accumulate_up_to_the_captured_amount(self, order, cod):
        payment = _captured(order, cod)
        for _ in range(4):
            services.refund(payment, Decimal("250.00"), reason="دفعة إرجاع")
        payment.refresh_from_db()
        assert payment.refunded_amount == Decimal("1000.00")
        assert payment.state == PaymentState.REFUNDED

    def test_over_refund_is_refused(self, order, cod):
        """FR-075: a refund larger than the capture is refused and writes nothing."""
        payment = _captured(order, cod)
        with pytest.raises(services.OverRefund):
            services.refund(payment, Decimal("1000.01"), reason="أكثر من المحصّل")
        assert not Refund.objects.exists()

    def test_refund_beyond_the_remainder_is_refused(self, order, cod):
        """FR-075: the bound is captured *minus already-refunded*, not captured.

        900 of 1000 is legitimate; a further 200 is not, even though 200 is far
        below the captured amount on its own.
        """
        payment = _captured(order, cod)
        services.refund(payment, Decimal("900.00"), reason="جزئي")
        with pytest.raises(services.OverRefund):
            services.refund(payment, Decimal("200.00"), reason="يتجاوز المتبقي")
        payment.refresh_from_db()
        assert payment.refunded_amount == Decimal("900.00")

    def test_uncaptured_payment_cannot_be_refunded(self, order, cod):
        payment = services.record_payment(
            order=order, method=cod, amount=Decimal("100.00"), idempotency_key="k"
        )
        with pytest.raises(ValidationError, match="غير محصّلة"):
            services.refund(payment, Decimal("50.00"), reason="لا")

    def test_zero_and_negative_refunds_are_refused(self, order, cod):
        payment = _captured(order, cod)
        for amount in ("0.00", "-1.00"):
            with pytest.raises(ValidationError):
                services.refund(payment, Decimal(amount), reason="لا")

    def test_the_database_refuses_a_refund_row_that_is_not_positive(self, order, cod):
        """FR-075 at the database, where the service cannot be gone around.

        The remaining balance is ``captured − Σ refunds``. A negative row written
        behind the service's back would *raise* that remainder and let the next
        refund exceed the capture, so ``refund_amount_positive`` is part of the
        bound — and unlike the model validators, which ``Refund.objects.create``
        never runs, PostgreSQL always checks it.
        """
        payment = _captured(order, cod)

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Refund.objects.create(
                    payment=payment,
                    amount=Decimal("-500.00"),
                    reason="تسميم الرصيد المتبقي",
                    state=RefundState.COMPLETED,
                )

        payment.refresh_from_db()
        assert payment.refunded_amount == Decimal("0.00")
        assert payment.refundable_amount == Decimal("1000.00")

    def test_refund_is_audited(self, order, cod):
        from apps.audit.models import AuditAction, AuditLog

        payment = _captured(order, cod)
        services.refund(payment, Decimal("10.00"), reason="اختبار")
        assert AuditLog.objects.filter(action=AuditAction.REFUND).exists()

    def test_refund_rows_record_who_and_why(self, order, cod):
        payment = _captured(order, cod)
        services.refund(payment, Decimal("10.00"), reason="منتج تالف")
        record = Refund.objects.get()
        assert record.reason == "منتج تالف"
        assert record.state == RefundState.COMPLETED


# ---------------------------------------------------------------------------
# T-1106 — reconciliation reports, never repairs
# ---------------------------------------------------------------------------


class TestReconciliation:
    def test_a_consistent_order_reports_nothing(self, order, cod):
        _captured(order, cod)
        assert services.reconcile(order) == []

    def test_a_hand_edited_status_is_reported(self, order, cod):
        _captured(order, cod)
        Order.objects.filter(pk=order.pk).update(payment_status=PaymentStatus.UNPAID)
        order.refresh_from_db()

        divergences = services.reconcile(order)
        assert any(d["field"] == "payment_status" for d in divergences)

    def test_reconciliation_does_not_mutate(self, order, cod):
        _captured(order, cod)
        Order.objects.filter(pk=order.pk).update(payment_status=PaymentStatus.UNPAID)
        services.reconcile(order)
        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.UNPAID, (
            "reconcile repaired the divergence instead of reporting it (FR-076)"
        )

    def test_the_management_command_reports_divergence_without_mutating(self, order, cod):
        """FR-076: `reconcile_payments` names the divergence and changes nothing.

        The requirement is about the *command*, so the command is what runs
        here — its report, its non-zero exit, and an untouched ledger afterwards.
        """
        _captured(order, cod)
        Order.objects.filter(pk=order.pk).update(payment_status=PaymentStatus.UNPAID)
        ledger_before = list(Payment.objects.values_list("pk", "state", "amount"))

        out = StringIO()
        with pytest.raises(CommandError):
            call_command("reconcile_payments", "--order", order.number, stdout=out)

        report = out.getvalue()
        assert order.number in report
        assert "payment_status" in report

        order.refresh_from_db()
        assert order.payment_status == PaymentStatus.UNPAID, (
            "the command repaired the divergence it was asked to report"
        )
        assert list(Payment.objects.values_list("pk", "state", "amount")) == ledger_before

    def test_the_management_command_stays_quiet_when_the_ledger_agrees(self, order, cod):
        """FR-076: a consistent order reconciles cleanly and exits zero."""
        _captured(order, cod)

        out = StringIO()
        call_command("reconcile_payments", "--order", order.number, stdout=out)

        assert "No divergence" in out.getvalue()


# ---------------------------------------------------------------------------
# T-1107 — provider callbacks, with no provider connected
# ---------------------------------------------------------------------------


class TestWebhookSkeleton:
    def test_duplicate_provider_event_is_recorded_once(self, order, cod):
        payment = _captured(order, cod)
        first = services.handle_provider_event(
            payment, provider_event_id="evt_1", event_type="captured", payload={"a": 1}
        )
        second = services.handle_provider_event(
            payment, provider_event_id="evt_1", event_type="captured", payload={"a": 1}
        )
        assert first is not None and second is None
        assert PaymentEvent.objects.filter(provider_event_id="evt_1").count() == 1

    def test_event_without_an_id_is_rejected(self, order, cod):
        payment = _captured(order, cod)
        with pytest.raises(services.WebhookRejected):
            services.handle_provider_event(
                payment, provider_event_id="", event_type="x", payload={}
            )

    def test_signature_verification_rejects_a_wrong_signature(self):
        body = b'{"amount": 100}'
        assert services.verify_signature("secret", body, "deadbeef") is False

    def test_signature_verification_accepts_the_right_one(self):
        import hashlib
        import hmac

        body = b'{"amount": 100}'
        signature = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
        assert services.verify_signature("secret", body, signature) is True

    def test_missing_secret_never_verifies(self):
        assert services.verify_signature("", b"x", "anything") is False

    def test_only_a_digest_of_the_payload_is_stored(self, order, cod):
        payment = _captured(order, cod)
        services.handle_provider_event(
            payment,
            provider_event_id="evt_2",
            event_type="captured",
            payload={"pan": "4111111111111111"},
        )
        event = PaymentEvent.objects.get(provider_event_id="evt_2")
        assert "4111" not in event.payload_digest
        assert len(event.payload_digest) == 64


# ---------------------------------------------------------------------------
# T-1108 — no card data anywhere
# ---------------------------------------------------------------------------


class TestNoCardData:
    FORBIDDEN = {
        "card_number", "cardnumber", "pan", "cvv", "cvc", "card_cvv",
        "expiry_month", "expiry_year", "cardholder", "card_holder",
    }

    def test_no_model_field_can_hold_card_data(self):
        from django.apps import apps as django_apps

        offenders = []
        for model in django_apps.get_models():
            for field in model._meta.get_fields():
                name = getattr(field, "name", "").lower()
                if name in self.FORBIDDEN:
                    offenders.append(f"{model._meta.label}.{name}")
        assert offenders == [], f"models expose card-data fields: {offenders}"

    def test_no_payment_form_accepts_card_data(self):
        from storefront import checkout_forms

        fields = set(checkout_forms.CheckoutForm().fields)
        assert not (fields & self.FORBIDDEN), "checkout collects card data"
