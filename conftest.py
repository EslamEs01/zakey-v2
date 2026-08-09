"""Shared pytest fixtures.

Every test runs against PostgreSQL. SQLite is refused outright because it
silently ignores ``SELECT ... FOR UPDATE`` and does not enforce the deferred
constraint semantics the commerce invariants rely on, so a green SQLite run
would be a false negative (FR-002, NFR-005).
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.conf import settings


def pytest_configure(config):  # noqa: ARG001
    engine = settings.DATABASES["default"]["ENGINE"]
    if "postgresql" not in engine:
        raise pytest.UsageError(
            f"ZAKEY tests require PostgreSQL; got {engine!r}. "
            "SQLite cannot verify locking or concurrency (NFR-005)."
        )


@pytest.fixture(autouse=True)
def _isolate_cache():
    """Clear the cache around every test.

    Rate limiting, lockouts and reset throttles are cache-backed and keyed on
    the *email and IP under test*, which are module-level constants reused by
    every test in a file. Without this, one test's lockout leaks into the next
    and the suite's result depends on execution order — a green run would prove
    nothing about FR-058.
    """
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def seeded_catalogue(db):
    """Seed the approved demonstration catalogue for THIS test only.

    The storefront is database-backed now (T-1601–T-1603), so route and
    rendering tests need real rows.

    Seeding happens inside the test's own transaction and is rolled back with
    it. That is deliberately not the cheapest option: a session-scoped commit
    would be faster, but it would also be visible to every other test, and the
    unit and concurrency suites build their own rows on the same natural keys
    (``cairo``, ``fingerprint``, ``zakey-apex-pro``). Sharing seeded state
    between them makes the result depend on execution order, which is exactly
    the property a test suite must not have.
    """
    from django.core.management import call_command

    call_command("seed_demo", verbosity=0)


@pytest.fixture
def storefront(seeded_catalogue):
    """A Django test client pointed at the seeded storefront."""
    from django.test import Client

    return Client()


@pytest.fixture
def site_setting(db):
    from apps.core.models import SiteSetting

    return SiteSetting.objects.get_solo()


@pytest.fixture
def governorate(db):
    from apps.shipping.models import Governorate

    return Governorate.objects.create(key="cairo", name="القاهرة", position=1)


@pytest.fixture
def area(db, governorate):
    from apps.shipping.models import ServiceArea

    return ServiceArea.objects.create(
        key="cairo-nasr-city",
        governorate=governorate,
        name="مدينة نصر",
        same_day_eligible=True,
        installation_eligible=True,
    )


@pytest.fixture
def category(db):
    from apps.catalog.models import Category
    from apps.core.models import PublicationStatus

    return Category.objects.create(
        slug="fingerprint", name="أقفال بالبصمة", status=PublicationStatus.PUBLISHED
    )


@pytest.fixture
def product(db, category):
    from apps.catalog.models import Product
    from apps.core.models import PublicationStatus
    from django.utils import timezone

    return Product.objects.create(
        slug="zakey-apex-pro",
        name="قفل زاكي أبيكس برو",
        short_description="قفل رئيسي فاخر",
        category=category,
        status=PublicationStatus.PUBLISHED,
        published_at=timezone.now(),
    )


@pytest.fixture
def variant(db, product):
    """Default variant, priced VAT-inclusive like the approved catalogue."""
    from apps.catalog.models import ProductVariant

    return ProductVariant.objects.create(
        product=product,
        sku="ZK-APEX-OBSIDIAN",
        finish_id="finish-obsidian",
        finish_label="أسود أوبسيديان",
        price=Decimal("7490.00"),
        is_default=True,
        position=0,
    )


@pytest.fixture
def second_variant(db, product):
    """A second finish of the SAME product - the prototype's blind spot."""
    from apps.catalog.models import ProductVariant

    return ProductVariant.objects.create(
        product=product,
        sku="ZK-APEX-CHAMPAGNE",
        finish_id="finish-champagne",
        finish_label="ذهبي شامبين",
        price=Decimal("7490.00"),
        position=1,
    )


@pytest.fixture
def stock(db, variant):
    from apps.inventory.models import StockItem

    return StockItem.objects.create(variant=variant, on_hand=25, reserved=0)


@pytest.fixture
def second_stock(db, second_variant):
    from apps.inventory.models import StockItem

    return StockItem.objects.create(variant=second_variant, on_hand=25, reserved=0)


@pytest.fixture
def user(db):
    """A bare registered user with no profile row.

    Some tests exercise the profile-less path deliberately (confirm/reset
    tokens harden against it); tests needing a profile use ``customer``.
    """
    from apps.accounts.models import User

    return User.objects.create_user(email="nada@example.com", password="StrongPass!234")


@pytest.fixture
def customer(db, user):
    from apps.accounts.models import CustomerProfile

    return CustomerProfile.objects.create(
        user=user, full_name="ندى إبراهيم", phone="01012345678"
    )


@pytest.fixture
def other_customer(db):
    from apps.accounts.models import CustomerProfile, User

    other = User.objects.create_user(email="omar@example.com", password="StrongPass!234")
    return CustomerProfile.objects.create(user=other, full_name="عمر حسن", phone="01112345678")
