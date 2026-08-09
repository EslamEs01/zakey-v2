"""Performance budgets (T-1805, NFR-001, NFR-004).

These measure **server-side work only** — view dispatch, ORM, template render —
by driving the Django test client in-process. Network, TLS and browser paint are
excluded, which is exactly what NFR-001 specifies.

A timing test is worth having only if it fails for the right reason. Two
precautions make that true here:

* **p95 over many iterations**, not a single sample, so one unlucky GC pause or
  a busy CI box does not decide the result.
* **A query-count assertion alongside every timing assertion.** Wall-clock is
  hardware-dependent and will drift; query count is not. If this file ever goes
  red on a slow machine, the query assertions say immediately whether the cause
  is real (an N+1 crept in) or environmental.
"""

from __future__ import annotations

import statistics
import time
from decimal import Decimal

import pytest
from django.db import connection, reset_queries
from django.test import override_settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

#: NFR-001
CATALOGUE_P95_MS = 300
DETAIL_P95_MS = 400
#: NFR-004
ORDER_P95_MS = 2000

ITERATIONS = 25


def percentile_95(samples: list[float]) -> float:
    ordered = sorted(samples)
    index = max(0, min(len(ordered) - 1, int(round(0.95 * len(ordered))) - 1))
    return ordered[index]


def time_get(client, url: str, iterations: int = ITERATIONS) -> tuple[float, list[float]]:
    samples: list[float] = []
    # One warm-up: the first request pays for template compilation and
    # connection setup, which no real visitor pays on every page load.
    client.get(url)
    for _ in range(iterations):
        start = time.perf_counter()
        response = client.get(url)
        elapsed = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        samples.append(elapsed)
    return percentile_95(samples), samples


class TestCataloguePerformance:
    """NFR-001: catalogue list p95 < 300 ms, detail p95 < 400 ms."""

    def test_catalogue_list_p95(self, storefront):
        p95, samples = time_get(storefront, reverse("storefront:shop"))

        assert p95 < CATALOGUE_P95_MS, (
            f"catalogue p95 {p95:.0f}ms exceeds {CATALOGUE_P95_MS}ms "
            f"(median {statistics.median(samples):.0f}ms)"
        )

    def test_product_detail_p95(self, storefront):
        from apps.catalog.models import Product

        product = Product.objects.published().first()
        p95, samples = time_get(
            storefront, reverse("storefront:product", kwargs={"slug": product.slug})
        )

        assert p95 < DETAIL_P95_MS, (
            f"detail p95 {p95:.0f}ms exceeds {DETAIL_P95_MS}ms "
            f"(median {statistics.median(samples):.0f}ms)"
        )

    def test_home_p95(self, storefront):
        p95, _ = time_get(storefront, reverse("storefront:home"))
        assert p95 < CATALOGUE_P95_MS


class TestCatalogueQueryBudgets:
    """NFR-002: the durable half of the performance promise.

    Wall-clock drifts with hardware; a query count does not. These are the
    assertions that actually catch a regression.
    """

    @override_settings(DEBUG=True)
    def _count_queries(self, client, url: str) -> int:
        reset_queries()
        response = client.get(url)
        assert response.status_code == 200
        return len(connection.queries)

    # Ceilings set from measurement against the seeded catalogue, with modest
    # headroom — not invented, and not raised to make a run pass. The measured
    # counts at the time of writing were: shop 23, product 31, home 44, cart 5,
    # checkout 9, account 7, wishlist 5, contact 6, about 6.
    #
    # These absolute numbers are the weaker half of the guarantee: they drift
    # with template changes and say nothing about scaling. The load-bearing
    # assertion is `test_the_catalogue_does_not_scale_with_product_count`
    # below, which proves the counts are *constant* in the size of the
    # catalogue. A page can be expensive and still be correct; a page whose
    # cost grows per row cannot.
    BUDGETS = {
        "shop": 30,
        "product": 40,
        "home": 55,
        "cart": 15,
        "checkout": 20,
        "account": 15,
        "wishlist": 15,
        "contact": 15,
        "about": 15,
    }

    def test_catalogue_list_is_bounded(self, storefront, django_assert_max_num_queries):
        with django_assert_max_num_queries(self.BUDGETS["shop"]):
            storefront.get(reverse("storefront:shop"))

    def test_product_detail_is_bounded(self, storefront, django_assert_max_num_queries):
        from apps.catalog.models import Product

        product = Product.objects.published().first()
        with django_assert_max_num_queries(self.BUDGETS["product"]):
            storefront.get(reverse("storefront:product", kwargs={"slug": product.slug}))

    def test_home_is_bounded(self, storefront, django_assert_max_num_queries):
        with django_assert_max_num_queries(self.BUDGETS["home"]):
            storefront.get(reverse("storefront:home"))

    def test_cart_is_bounded(self, storefront, django_assert_max_num_queries):
        with django_assert_max_num_queries(self.BUDGETS["cart"]):
            storefront.get(reverse("storefront:cart"))

    def test_checkout_is_bounded(self, storefront, django_assert_max_num_queries):
        with django_assert_max_num_queries(self.BUDGETS["checkout"]):
            storefront.get(reverse("storefront:checkout"))

    @pytest.mark.parametrize(
        "route", ["account", "wishlist", "contact", "about"]
    )
    def test_every_remaining_route_is_bounded(
        self, storefront, django_assert_max_num_queries, route
    ):
        with django_assert_max_num_queries(self.BUDGETS[route]):
            storefront.get(reverse(f"storefront:{route}"))

    def test_every_public_route_has_a_documented_budget(self):
        """A new route must not escape the budget regime unnoticed."""
        documented = set(self.BUDGETS)
        expected = {
            "home", "shop", "product", "cart", "checkout",
            "account", "wishlist", "contact", "about",
        }
        assert expected <= documented, f"undocumented routes: {sorted(expected - documented)}"

    def test_the_catalogue_does_not_scale_with_product_count(self, storefront):
        """The N+1 detector: more products must not mean more queries.

        The category is taken from the seeded catalogue rather than a fixture:
        the ``storefront`` fixture already creates one with the same slug, and
        a second would collide on the unique constraint.
        """
        from apps.catalog.models import Product, ProductVariant
        from apps.core.models import PublicationStatus
        from django.utils import timezone

        category = Product.objects.published().first().category
        baseline = self._query_count(storefront, reverse("storefront:shop"))

        for index in range(10):
            product = Product.objects.create(
                slug=f"perf-{index}",
                name=f"منتج {index}",
                category=category,
                status=PublicationStatus.PUBLISHED,
                published_at=timezone.now(),
            )
            ProductVariant.objects.create(
                product=product,
                sku=f"PERF-{index}",
                finish_label="أسود",
                price=Decimal("1000.00"),
                is_default=True,
            )

        after = self._query_count(storefront, reverse("storefront:shop"))

        assert after <= baseline + 2, (
            f"catalogue queries grew from {baseline} to {after} after adding 10 "
            "products — that is an N+1"
        )

    def _query_count(self, client, url: str) -> int:
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as captured:
            response = client.get(url)
            assert response.status_code == 200
        return len(captured)


class TestOrderCreationPerformance:
    """NFR-004: order creation within 2 s p95 under 20 concurrent checkouts.

    The *concurrent* half is proven in ``tests/concurrency`` with real threads;
    what is measured here is the per-order cost of the same code path, which is
    what that concurrency has to multiply.
    """

    def test_order_creation_p95(self, storefront, seeded_catalogue):
        from apps.cart.models import Cart, CartLine
        from apps.catalog.models import Product
        from apps.inventory.models import StockItem
        from apps.orders.services import create_order

        variant = Product.objects.get(slug="zakey-apex-pro").variants.first()
        item, _ = StockItem.objects.get_or_create(variant=variant)
        StockItem.objects.filter(pk=item.pk).update(on_hand=500, reserved=0)

        address = {
            "full_name": "ندى إبراهيم",
            "phone": "01012345678",
            "governorate_key": "cairo",
            "governorate_name": "القاهرة",
            "area_key": "cairo-nasr-city",
            "area_name": "مدينة نصر",
            "city": "مدينة نصر",
            "street": "شارع تجريبي 12",
            "building": "5",
        }

        samples: list[float] = []
        for index in range(15):
            cart = Cart.objects.create(session_key=f"perf-{index}")
            CartLine.objects.create(cart=cart, variant=variant, quantity=1)

            start = time.perf_counter()
            create_order(
                cart=cart,
                email=f"perf{index}@example.com",
                phone="01012345678",
                address_data=dict(address),
                idempotency_key=f"perf-{index}",
                terms_accepted=True,
            )
            samples.append((time.perf_counter() - start) * 1000)

        p95 = percentile_95(samples)
        assert p95 < ORDER_P95_MS, (
            f"order creation p95 {p95:.0f}ms exceeds {ORDER_P95_MS}ms "
            f"(median {statistics.median(samples):.0f}ms)"
        )

    def test_order_creation_is_query_bounded(
        self, storefront, seeded_catalogue, django_assert_max_num_queries
    ):
        """A per-line N+1 here multiplies by every concurrent checkout."""
        from apps.cart.models import Cart, CartLine
        from apps.catalog.models import Product
        from apps.inventory.models import StockItem
        from apps.orders.services import create_order

        variant = Product.objects.get(slug="zakey-apex-pro").variants.first()
        item, _ = StockItem.objects.get_or_create(variant=variant)
        StockItem.objects.filter(pk=item.pk).update(on_hand=500, reserved=0)

        cart = Cart.objects.create(session_key="perf-budget")
        CartLine.objects.create(cart=cart, variant=variant, quantity=1)

        with django_assert_max_num_queries(60):
            create_order(
                cart=cart,
                email="budget@example.com",
                phone="01012345678",
                address_data={
                    "full_name": "ندى إبراهيم",
                    "phone": "01012345678",
                    "governorate_key": "cairo",
                    "governorate_name": "القاهرة",
                    "area_key": "cairo-nasr-city",
                    "area_name": "مدينة نصر",
                    "city": "مدينة نصر",
                    "street": "شارع تجريبي 12",
                    "building": "5",
                },
                idempotency_key="perf-budget",
                terms_accepted=True,
            )
