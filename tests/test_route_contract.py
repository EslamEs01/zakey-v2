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


def test_all_thirteen_public_routes_return_expected_status(storefront):
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
