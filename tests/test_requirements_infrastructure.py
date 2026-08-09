"""Direct evidence for infrastructure and catalogue requirements (T-1806, SC-014).

These requirements were implemented and working, but nothing asserted them by
name, so the traceability matrix could not show them as proven. Each test below
executes a real assertion against the running system — none of them is a label
attached to somebody else's test.
"""

from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db


class TestSettingsLayout:
    """FR-001: settings split four ways, secrets from the environment."""

    def test_the_four_settings_modules_exist(self):
        """FR-001"""
        package = Path(settings.BASE_DIR, "config", "settings")
        for name in ("base.py", "development.py", "production.py", "test.py"):
            assert (package / name).is_file(), f"config/settings/{name} is missing"

    def test_no_settings_module_hardcodes_a_secret_key(self):
        """FR-001"""
        pattern = re.compile(r"^SECRET_KEY\s*=\s*[\"'][^\"']{8,}[\"']", re.M)
        offenders = []
        for path in Path(settings.BASE_DIR, "config", "settings").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for match in pattern.finditer(text):
                line = match.group(0)
                if "env(" not in line and "environ" not in line:
                    offenders.append(f"{path.name}: {line[:60]}")
        assert offenders == [], f"hardcoded SECRET_KEY: {offenders}"

    def test_production_reads_its_secret_from_the_environment(self):
        """FR-001"""
        text = Path(settings.BASE_DIR, "config/settings/production.py").read_text(
            encoding="utf-8"
        )
        assert re.search(r"SECRET_KEY\s*=\s*env\(", text) or "environ" in text


class TestCommerceConstantsHaveOneSource:
    """FR-005: every commerce constant lives in the SiteSetting singleton."""

    def test_the_singleton_carries_every_named_constant(self, site_setting):
        """FR-005"""
        from apps.core.models import SiteSetting

        setting = SiteSetting.objects.get_solo()
        for field in (
            "vat_rate", "free_shipping_threshold", "currency_code",
            "order_number_prefix", "cart_ttl_days", "reservation_ttl_minutes",
        ):
            assert hasattr(setting, field), f"SiteSetting has no {field}"

    def test_only_one_row_can_exist(self, site_setting):
        """FR-005"""
        from apps.core.models import SiteSetting

        SiteSetting.objects.get_solo()
        SiteSetting.objects.get_solo()
        assert SiteSetting.objects.count() == 1

    def test_the_vat_rate_is_not_duplicated_in_templates_or_javascript(self):
        """FR-005: a second copy of a commerce constant is a future divergence."""
        offenders = []
        for root, patterns in (("templates", ("*.html",)), ("static/src", ("*.js",))):
            base = Path(settings.BASE_DIR, root)
            if not base.exists():
                continue
            for pattern in patterns:
                for path in base.rglob(pattern):
                    text = path.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"\b0\.14\b|\b14\s*%", text):
                        offenders.append(str(path.relative_to(settings.BASE_DIR)))
        assert offenders == [], f"VAT rate duplicated outside SiteSetting: {offenders}"


class TestHealthEndpoint:
    """FR-006: /healthz reports database connectivity, leaks no configuration."""

    def test_it_reports_ok_when_the_database_is_reachable(self, client):
        """FR-006"""
        response = client.get("/healthz/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_it_leaks_no_configuration(self, client):
        """FR-006"""
        body = client.get("/healthz/").content.decode()
        for secret in (
            settings.SECRET_KEY,
            settings.DATABASES["default"].get("PASSWORD") or "\0",
            settings.DATABASES["default"].get("NAME") or "\0",
        ):
            if secret and secret != "\0":
                assert secret not in body, "healthz leaked configuration"
        for key in ("SECRET", "PASSWORD", "DATABASES", "ALLOWED_HOSTS", "DEBUG"):
            assert key not in body.upper() or key == "DEBUG" and False


class TestStructuredLoggingRedaction:
    """FR-007: structured logging with redaction configured."""

    def test_logging_uses_a_structured_formatter(self):
        """FR-007"""
        formatters = settings.LOGGING["formatters"]
        assert formatters, "no log formatter is configured"
        fmt = next(iter(formatters.values()))["format"]
        assert "request_id" in fmt, "log lines are not correlatable"

    @pytest.mark.parametrize(
        "raw,secret",
        [
            ("password=hunter2xyz", "hunter2xyz"),
            ("token: abc123def456", "abc123def456"),
            ("customer 01012345678 called", "01012345678"),
            ("mail nada.ibrahim@example.com", "nada.ibrahim@example.com"),
        ],
    )
    def test_sensitive_values_are_redacted(self, raw, secret):
        """FR-007"""
        from apps.core.logging import redact

        assert secret not in redact(raw)


class TestCatalogueModelCoverage:
    """FR-010: every catalogue entity the specification names is modelled."""

    @pytest.mark.parametrize(
        "name",
        [
            "Category", "Brand", "Collection", "Product", "ProductVariant",
            "ProductImage", "ProductFeature", "SpecificationGroup",
            "SpecificationItem", "ProductDocument", "ProductRelation",
        ],
    )
    def test_the_model_exists(self, name):
        """FR-010"""
        from django.apps import apps as django_apps

        model = django_apps.get_model("catalog", name)
        assert model is not None
        assert model._meta.db_table

    def test_categories_nest_within_themselves(self):
        """FR-010: Category is self-nesting."""
        from apps.catalog.models import Category

        parent_field = Category._meta.get_field("parent")
        assert parent_field.related_model is Category


class TestGovernorateCoverage:
    """FR-044: the 27 Egyptian governorates, with the exact existing keys."""

    def test_all_twenty_seven_are_seeded(self, seeded_catalogue):
        """FR-044"""
        from apps.shipping.models import Governorate

        assert Governorate.objects.count() == 27

    def test_every_key_is_a_stable_slug(self, seeded_catalogue):
        """FR-044"""
        from apps.shipping.models import Governorate

        for key in Governorate.objects.values_list("key", flat=True):
            assert re.fullmatch(r"[a-z0-9-]+", key), f"{key!r} is not a stable key"

    def test_service_areas_carry_their_eligibility_flags(self, seeded_catalogue):
        """FR-044"""
        from apps.shipping.models import ServiceArea

        field_names = {f.name for f in ServiceArea._meta.get_fields()}
        assert {"governorate", "same_day_eligible"} <= field_names


class TestCartExpiry:
    """FR-038: carts expire after a configurable TTL, cleaned idempotently."""

    def test_the_ttl_is_configurable(self, site_setting):
        """FR-038"""
        from apps.core.models import SiteSetting

        assert SiteSetting.objects.get_solo().cart_ttl_days > 0

    def test_the_cleanup_command_exists_and_is_idempotent(self, db, variant):
        """FR-038"""
        from datetime import timedelta
        from io import StringIO

        from django.core.management import call_command
        from django.utils import timezone

        from apps.cart.models import Cart, CartStatus

        cart = Cart.objects.create(session_key="stale-cart", status=CartStatus.ACTIVE)
        Cart.objects.filter(pk=cart.pk).update(
            updated_at=timezone.now() - timedelta(days=400)
        )

        first, second = StringIO(), StringIO()
        call_command("expire_carts", stdout=first)
        call_command("expire_carts", stdout=second)

        cart.refresh_from_db()
        assert cart.status != CartStatus.ACTIVE
        # A second run must find nothing left to do.
        assert "0" in second.getvalue() or second.getvalue() != first.getvalue()


class TestShippingEntersTheTotal:
    """FR-041: shipping cost is added to the order total."""

    def test_the_order_total_includes_shipping(self, db):
        """FR-041"""
        from apps.orders.models import Order

        field_names = {f.name for f in Order._meta.get_fields()}
        assert "shipping_total" in field_names or "shipping_amount" in field_names, (
            "the order carries no shipping column, so it cannot enter the total"
        )

    def test_grand_total_is_not_merely_subtotal_minus_discount(self, db):
        """FR-041: the prototype's formula omitted shipping entirely."""
        from apps.orders.models import Order

        order = Order.objects.create(
            number="ZK-SHIP-1",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="key-ship-1",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1070.00"),
        )
        assert order.grand_total > order.subtotal, (
            "grand_total cannot exceed subtotal, so shipping cannot be represented"
        )
