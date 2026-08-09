"""Executable freeze of the public route/slug contract (task T-0103).

This is the guard every later phase must keep green (re-verified in T-1907,
SC-009, SC-011):

* all 13 public named routes resolve and return their expected status
  (200 for pages, 404 for ``errors/404/``, 500 for ``errors/500/``);
* every stable slug in ``apps/core/seed_data/approved-catalogue.json`` stays
  ``reverse()``-resolvable for ``/collections/<slug>/`` and
  ``/products/<slug>/`` and renders (a disappearing slug fails loudly);
* the catalogue keeps its frozen shape: 9 products / 6 collections /
  4 categories.

Storefront views render from the database now, so these tests run against the
seeded demonstration catalogue (see the ``storefront`` fixture in conftest.py).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.test import Client  # noqa: F401  (kept for typing/back-compat)
from django.urls import reverse

FIXTURE_PATH = (
    Path(__file__).resolve().parent.parent
    / "apps"
    / "core"
    / "seed_data"
    / "approved-catalogue.json"
)

EXPECTED_PRODUCT_COUNT = 9
EXPECTED_COLLECTION_COUNT = 6
EXPECTED_CATEGORY_COUNT = 4


@pytest.fixture(scope="module")
def fixture_payload():
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


# All 13 public named routes, with the args needed to reverse them and the
# status each one must return. Route names are part of the contract.
ROUTE_EXPECTATIONS = (
    {"name": "storefront:home", "status": 200},
    {"name": "storefront:shop", "status": 200},
    {
        "name": "storefront:collection",
        "kwargs": {"slug": "fingerprint-locks"},
        "status": 200,
    },
    {
        "name": "storefront:search",
        "query": {"q": "ذكي"},
        "status": 200,
    },
    {
        "name": "storefront:product",
        "kwargs": {"slug": "zakey-apex-pro"},
        "status": 200,
    },
    {"name": "storefront:cart", "status": 200},
    {"name": "storefront:checkout", "status": 200},
    {"name": "storefront:wishlist", "status": 200},
    {
        "name": "storefront:account",
        "query": {"state": "signed-in"},
        "status": 200,
    },
    {"name": "storefront:about", "status": 200},
    {"name": "storefront:contact", "status": 200},
    {"name": "storefront:error-404", "status": 404},
    {"name": "storefront:error-500", "status": 500},
)

# The literal URL every route name must keep producing. ``reverse()`` returning
# *something* only proves the name still exists: rename ``path("shop/")`` to
# ``path("store/")`` and every reverse-based assertion in this file still
# passes, while every bookmark, inbound link and indexed result breaks. The
# URLs are half of what FR-131 protects, so they are frozen literally.
FROZEN_URLS = {
    "storefront:home": "/",
    "storefront:shop": "/shop/",
    "storefront:collection": "/collections/fingerprint-locks/",
    "storefront:search": "/search/",
    "storefront:product": "/products/zakey-apex-pro/",
    "storefront:cart": "/cart/",
    "storefront:checkout": "/checkout/",
    "storefront:wishlist": "/wishlist/",
    "storefront:account": "/account/",
    "storefront:about": "/about/",
    "storefront:contact": "/contact/",
    "storefront:error-404": "/errors/404/",
    "storefront:error-500": "/errors/500/",
}


def test_every_route_name_reverses_to_its_frozen_url():
    """The name → URL mapping is itself the contract (FR-131).

    No database and no rendering: this is purely "did the URL move?", which is
    the question a reverse-and-fetch test cannot answer on its own.
    """
    assert set(FROZEN_URLS) == {expected["name"] for expected in ROUTE_EXPECTATIONS}, (
        "the frozen URL table and the route table disagree about which routes exist"
    )
    for expected in ROUTE_EXPECTATIONS:
        name = expected["name"]
        assert reverse(name, kwargs=expected.get("kwargs")) == FROZEN_URLS[name], (
            f"{name} no longer lives at {FROZEN_URLS[name]}"
        )


def test_all_thirteen_public_routes_return_expected_status(storefront):
    """Every public route name still resolves and still answers identically (FR-131)."""
    client = storefront
    assert len(ROUTE_EXPECTATIONS) == 13
    for expected in ROUTE_EXPECTATIONS:
        url = reverse(expected["name"], kwargs=expected.get("kwargs"))
        response = client.get(url, expected.get("query", {}))
        assert response.status_code == expected["status"], (
            f"{expected['name']} ({url}) returned {response.status_code}, "
            f"expected {expected['status']}"
        )


def test_fixture_counts_remain_frozen(fixture_payload):
    assert len(fixture_payload["products"]) == EXPECTED_PRODUCT_COUNT, (
        "products count changed: "
        f"{len(fixture_payload['products'])} != {EXPECTED_PRODUCT_COUNT}"
    )
    assert len(fixture_payload["collections"]) == EXPECTED_COLLECTION_COUNT, (
        "collections count changed: "
        f"{len(fixture_payload['collections'])} != {EXPECTED_COLLECTION_COUNT}"
    )
    assert len(fixture_payload["categories"]) == EXPECTED_CATEGORY_COUNT, (
        "categories count changed: "
        f"{len(fixture_payload['categories'])} != {EXPECTED_CATEGORY_COUNT}"
    )


@pytest.mark.parametrize(
    "slug",
    [
        "best-sellers",
        "featured",
        "fingerprint-locks",
        "smart-door-locks",
        "smart-home-solutions",
        "security-accessories",
    ],
)
def test_collection_slug_stays_resolvable_and_renders(storefront, fixture_payload, slug):
    """A collection keeps its ``/collections/<slug>/`` URL and still renders (FR-131)."""
    _assert_slug_present(fixture_payload, "collections", slug)
    url = reverse("storefront:collection", kwargs={"slug": slug})
    assert url == f"/collections/{slug}/"
    response = storefront.get(url)
    assert response.status_code == 200, (
        f"/collections/{slug}/ returned {response.status_code}; "
        "a fixture slug must keep rendering"
    )


@pytest.mark.parametrize(
    "slug",
    [
        "zakey-apex-pro",
        "zakey-nexus-elite",
        "zakey-vision-x",
        "zakey-pulse-f5",
        "zakey-orbit-k3",
        "zakey-nova-s2",
        "zakey-core-c1",
        "zakey-guard-view",
        "zakey-bridge-mini",
    ],
)
def test_product_slug_stays_resolvable_and_renders(storefront, fixture_payload, slug):
    """A product keeps its ``/products/<slug>/`` URL and still renders (FR-131)."""
    _assert_slug_present(fixture_payload, "products", slug)
    url = reverse("storefront:product", kwargs={"slug": slug})
    assert url == f"/products/{slug}/"
    response = storefront.get(url)
    assert response.status_code == 200, (
        f"/products/{slug}/ returned {response.status_code}; "
        "a fixture slug must keep rendering"
    )


def _assert_slug_present(fixture_payload, section, slug):
    slugs = {item["slug"] for item in fixture_payload[section]}
    assert slug in slugs, (
        f"slug {slug!r} disappeared from fixture {section!r}: {sorted(slugs)}"
    )
