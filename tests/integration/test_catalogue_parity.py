"""Catalogue parity: database selectors vs. the approved prototype (T-0509).

The storefront's catalogue moved from ``storefront.fixture_provider`` to
``apps.catalog.selectors``. This suite is the evidence that the move changed the
*source* and nothing else: for every canonical query the two must agree on which
products appear, in what order, on which page, and with what result state.

The oracle it compares against (``tests/fixtures/reference_catalogue``) is the
approved prototype's own query logic, kept under ``tests/`` where it cannot be
imported by a shipped app. The runtime provider that used to serve requests is
deleted (T-1608); this file is what proves the database took its behaviour over
faithfully, so it should be the last thing deleted, not the first.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.catalog import selectors
from tests.fixtures import reference_catalogue as reference

pytestmark = pytest.mark.django_db


def _plain(value):
    """Normalise Decimal/int/float so 7490 and Decimal('7490.00') compare equal."""
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_plain(item) for item in value]
    return value


#: Canonical catalogue queries: no filter, each sort, pagination edges, search
#: hit and miss, each facet, and the reversed-price-bounds repair.
CANONICAL_QUERIES = [
    pytest.param({}, id="unfiltered"),
    pytest.param({"sort": "featured"}, id="sort-featured"),
    pytest.param({"sort": "price-asc"}, id="sort-price-asc"),
    pytest.param({"sort": "price-desc"}, id="sort-price-desc"),
    pytest.param({"sort": "name"}, id="sort-name"),
    pytest.param({"sort": "not-a-sort"}, id="sort-unknown-falls-back"),
    pytest.param({"page": "2"}, id="page-2"),
    pytest.param({"page": "99"}, id="page-clamped-after-filtering"),
    pytest.param({"page": "0"}, id="page-floored-at-1"),
    pytest.param({"q": "زاكي"}, id="search-hit"),
    pytest.param({"q": "nothing-matches-this"}, id="search-miss"),
    pytest.param({"category": "fingerprint"}, id="facet-category"),
    pytest.param({"category": "not-a-category"}, id="facet-category-unknown"),
    pytest.param({"availability": "available"}, id="facet-available"),
    pytest.param({"availability": "unavailable"}, id="facet-unavailable"),
    pytest.param({"priceMin": "3000"}, id="price-min"),
    pytest.param({"priceMax": "3000"}, id="price-max"),
    pytest.param({"priceMin": "2500", "priceMax": "6000"}, id="price-band"),
    pytest.param({"priceMin": "5000", "priceMax": "3000"}, id="price-bounds-reversed"),
]

COLLECTION_SLUGS = [
    "best-sellers",
    "featured",
    "fingerprint-locks",
    "smart-door-locks",
    "smart-home-solutions",
    "security-accessories",
]


@pytest.mark.parametrize("query", CANONICAL_QUERIES)
def test_catalogue_matches_the_approved_prototype(seeded_catalogue, query):
    expected = reference.get_catalogue(query)
    actual = selectors.get_catalogue(query)

    assert [p["slug"] for p in actual["products"]] == [
        p["slug"] for p in expected["products"]
    ], "the page shows different products, or the same ones in a different order"
    for key in ("totalCount", "page", "pageCount", "pageSize", "state"):
        assert actual[key] == expected[key], f"{key} diverged"
    assert actual["activeChips"] == expected["activeChips"]


@pytest.mark.parametrize("slug", COLLECTION_SLUGS)
def test_every_collection_matches_the_approved_prototype(seeded_catalogue, slug):
    expected = reference.get_catalogue({}, slug)
    actual = selectors.get_catalogue({}, slug)

    assert [p["slug"] for p in actual["products"]] == [
        p["slug"] for p in expected["products"]
    ]
    assert actual["totalCount"] == expected["totalCount"]


def test_feature_facets_use_and_semantics(seeded_catalogue):
    """Two facets must narrow, never widen (AND, not OR)."""
    keys = [item["key"] for item in selectors._filter_features()][:2]
    if len(keys) < 2:
        pytest.skip("catalogue has fewer than two distinct feature facets")
    query = {"feature": keys}
    expected = reference.get_catalogue(query)
    actual = selectors.get_catalogue(query)

    assert [p["slug"] for p in actual["products"]] == [
        p["slug"] for p in expected["products"]
    ]
    single = selectors.get_catalogue({"feature": [keys[0]]})
    assert actual["totalCount"] <= single["totalCount"]


def test_filter_facet_universe_matches(seeded_catalogue):
    assert _plain(selectors._filter_features()) == _plain(
        reference.filter_features()
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
def test_product_card_fields_match_the_approved_prototype(seeded_catalogue, slug):
    """Every field the product card renders, per product (frontend-contract §3)."""
    expected = next(
        item
        for item in reference.load_reference()["products"]
        if item["slug"] == slug
    )
    actual = selectors.get_product_detail(slug)["product"]

    assert actual["name"] == expected["name"]
    assert actual["shortDescription"] == expected["shortDescription"]
    assert _plain(actual["price"]) == _plain(expected["price"])
    assert _plain(actual["compareAtPrice"]) == _plain(expected.get("compareAtPrice"))
    assert actual["badge"] == expected.get("badge")
    assert actual["availability"] == expected["availability"]
    assert actual["instalmentMessage"] == expected["instalmentMessage"]
    assert [image["path"] for image in actual["images"]] == [
        image["path"] for image in expected["images"]
    ]
    assert [image["alt"] for image in actual["images"]] == [
        image["alt"] for image in expected["images"]
    ]
    assert [finish["id"] for finish in actual["finishes"]] == [
        finish["id"] for finish in expected["finishes"]
    ]
    assert [feature["key"] for feature in actual["features"]] == [
        feature["key"] for feature in expected["features"]
    ]
    assert actual["serviceFlags"] == expected["serviceFlags"]


def test_availability_parity_including_limited(seeded_catalogue):
    """``limited`` counts as available in the facet, exactly as before (FR-018)."""
    fixture_products = reference.load_reference()["products"]
    by_slug = {item["slug"]: item["availability"] for item in fixture_products}

    for record in selectors.get_catalogue({})["products"]:
        assert record["availability"] == by_slug[record["slug"]]

    available = selectors.get_catalogue({"availability": "available"})
    assert available["totalCount"] == sum(
        1 for value in by_slug.values() if value in {"available", "limited"}
    )


def test_draft_products_never_reach_the_storefront(seeded_catalogue):
    """A selector, not a template, is what keeps unpublished stock invisible."""
    from apps.catalog.models import Product
    from apps.core.models import PublicationStatus

    product = Product.objects.get(slug="zakey-apex-pro")
    product.status = PublicationStatus.DRAFT
    product.save(update_fields=["status"])

    slugs = [p["slug"] for p in selectors.get_catalogue({})["products"]]
    assert "zakey-apex-pro" not in slugs
    assert selectors.get_product_detail("zakey-apex-pro") is None
