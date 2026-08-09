"""The approved storefront's catalogue behaviour, as a TEST-ONLY oracle (T-1608).

This is the logic that used to live in ``storefront/fixture_provider.py`` and
serve real requests. It is kept — and only kept — because it is the executable
record of how the approved prototype filtered, sorted, searched and paginated
the catalogue, which is what ``tests/integration/test_catalogue_parity.py``
compares the database implementation against.

Three properties make it safe to keep:

* it lives under ``tests/``, so it is not importable from any shipped app
  without the test suite being installed;
* nothing in ``apps/`` or ``storefront/`` imports it — asserted by
  ``test_no_runtime_module_reads_the_reference_dataset``;
* it is read-only. There is no write path, no ORM access and no request
  handling here, so it cannot become a source of commerce truth again.

The dataset itself lives with the seed command (``apps/core/seed_data/``),
because seeding a demonstration database is its one remaining *product* role
(T-1608: "keep the JSON as seed input only"). This module reads that same file
so the oracle and the seed can never drift apart.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

REFERENCE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "apps"
    / "core"
    / "seed_data"
    / "approved-catalogue.json"
)

ALLOWED_SORTS = {"featured", "price-asc", "price-desc", "name"}
PAGE_SIZE = 6


class ReferenceContractError(RuntimeError):
    """The authored dataset violates the approved frontend contract."""


@dataclass(frozen=True)
class CatalogueCriteria:
    q: str = ""
    category: str | None = None
    collection: str | None = None
    price_min: int | None = None
    price_max: int | None = None
    features: tuple[str, ...] = ()
    availability: str | None = None
    sort: str = "featured"
    page: int = 1


def _unique(records: list[dict[str, Any]], key: str, label: str) -> None:
    values = [record[key] for record in records]
    if len(values) != len(set(values)):
        raise ReferenceContractError(f"Duplicate {label} {key}")


def _require_local_asset(path: str) -> None:
    if path.startswith(("http://", "https://", "//")):
        raise ReferenceContractError(f"Remote asset is not allowed: {path}")


def _validate(data: dict[str, Any]) -> dict[str, Any]:
    required = {
        "meta", "site", "navigation", "categories", "collections", "products",
        "reviews", "faqs", "partners", "team", "governorates", "serviceEligibility",
        "shippingOptions", "paymentOptions", "prototypeAccounts", "prototypeCarts",
        "prototypeWishlists",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise ReferenceContractError(f"Missing sections: {', '.join(missing)}")
    if data["meta"].get("fixtureStatus") != "demonstration":
        raise ReferenceContractError("Reference dataset must be marked demonstration")

    for section in ("categories", "collections", "products", "reviews", "faqs"):
        _unique(data[section], "id", section)
    _unique(data["categories"], "slug", "categories")
    _unique(data["collections"], "slug", "collections")
    _unique(data["products"], "slug", "products")
    _unique(data["governorates"], "key", "governorates")
    if len(data["governorates"]) != 27:
        raise ReferenceContractError("Must contain exactly 27 governorates")

    category_ids = {item["id"] for item in data["categories"]}
    product_ids = {item["id"] for item in data["products"]}
    review_ids = {item["id"] for item in data["reviews"]}
    faq_ids = {item["id"] for item in data["faqs"]}
    for product in data["products"]:
        if product["categoryId"] not in category_ids:
            raise ReferenceContractError(f"Unknown category for {product['id']}")
        if not 2190 <= int(product["price"]) <= 7490:
            raise ReferenceContractError(f"Price outside approved range for {product['id']}")
        for image in product.get("images", []):
            _require_local_asset(image["path"])
        if not set(product.get("reviewIds", [])).issubset(review_ids):
            raise ReferenceContractError(f"Unknown review for {product['id']}")
        if not set(product.get("faqIds", [])).issubset(faq_ids):
            raise ReferenceContractError(f"Unknown FAQ for {product['id']}")
        related = set(product.get("relatedProductIds", []))
        if product["id"] in related or not related.issubset(product_ids):
            raise ReferenceContractError(f"Invalid related products for {product['id']}")

    for section in ("partners", "team"):
        for record in data[section]:
            asset = record.get("image") or record.get("mark")
            if asset:
                _require_local_asset(asset["path"] if isinstance(asset, dict) else asset)
    return data


@lru_cache(maxsize=1)
def load_reference() -> dict[str, Any]:
    with REFERENCE_PATH.open(encoding="utf-8") as handle:
        return _validate(json.load(handle))


def _integer(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def normalize_criteria(query: Mapping[str, Any], collection: str | None = None) -> CatalogueCriteria:
    data = load_reference()
    category_slugs = {item["slug"] for item in data["categories"]}
    collection_slugs = {item["slug"] for item in data["collections"]}
    feature_values = {
        feature["key"] for product in data["products"] for feature in product.get("features", [])
    }
    getlist = getattr(query, "getlist", None)
    requested_features = getlist("feature") if getlist else query.get("feature", [])
    if isinstance(requested_features, str):
        requested_features = [requested_features]
    price_min = _integer(query.get("priceMin"))
    price_max = _integer(query.get("priceMax"))
    if price_min is not None and price_max is not None and price_min > price_max:
        price_min, price_max = price_max, price_min
    sort = str(query.get("sort", "featured"))
    page = max(1, _integer(query.get("page")) or 1)
    category = str(query.get("category", "")) or None
    selected_collection = collection or str(query.get("collection", "")) or None
    availability = str(query.get("availability", "")) or None
    return CatalogueCriteria(
        q=" ".join(str(query.get("q", "")).split()),
        category=category if category in category_slugs else None,
        collection=selected_collection if selected_collection in collection_slugs else None,
        price_min=max(0, price_min) if price_min is not None else None,
        price_max=max(0, price_max) if price_max is not None else None,
        features=tuple(value for value in requested_features if value in feature_values),
        availability=availability if availability in {"available", "unavailable"} else None,
        sort=sort if sort in ALLOWED_SORTS else "featured",
        page=page,
    )


def get_catalogue(query: Mapping[str, Any], collection: str | None = None) -> dict[str, Any]:
    """The approved catalogue result for one query — the parity oracle."""
    data = load_reference()
    criteria = normalize_criteria(query, collection)
    products = list(data["products"])
    order = {product["id"]: index for index, product in enumerate(products)}
    categories = {item["id"]: item for item in data["categories"]}
    category_by_slug = {item["slug"]: item for item in data["categories"]}

    if criteria.collection:
        selected = next(i for i in data["collections"] if i["slug"] == criteria.collection)
        allowed = set(selected["productIds"])
        products = [p for p in products if p["id"] in allowed]
    if criteria.category:
        category_id = category_by_slug[criteria.category]["id"]
        products = [p for p in products if p["categoryId"] == category_id]
    if criteria.q:
        needle = criteria.q.casefold()
        products = [
            p for p in products
            if needle in " ".join([p["name"], p.get("shortDescription", "")]).casefold()
        ]
    if criteria.price_min is not None:
        products = [p for p in products if p["price"] >= criteria.price_min]
    if criteria.price_max is not None:
        products = [p for p in products if p["price"] <= criteria.price_max]
    if criteria.features:
        products = [
            p for p in products
            if set(criteria.features).issubset({f["key"] for f in p.get("features", [])})
        ]
    if criteria.availability == "available":
        products = [p for p in products if p["availability"] in {"available", "limited"}]
    elif criteria.availability == "unavailable":
        products = [p for p in products if p["availability"] == "unavailable"]

    if criteria.sort == "price-asc":
        products.sort(key=lambda i: (i["price"], order[i["id"]]))
    elif criteria.sort == "price-desc":
        products.sort(key=lambda i: (-i["price"], order[i["id"]]))
    elif criteria.sort == "name":
        products.sort(key=lambda i: (i["name"], order[i["id"]]))
    else:
        products.sort(key=lambda i: order[i["id"]])

    page_count = max(1, (len(products) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(criteria.page, page_count)
    offset = (page - 1) * PAGE_SIZE
    has_filters = any([
        criteria.category, criteria.collection, criteria.price_min,
        criteria.price_max, criteria.features, criteria.availability,
    ])
    state = "populated"
    if not products:
        state = "no-search-results" if criteria.q and not has_filters else "no-filtered-results"

    return {
        "criteria": criteria,
        "products": [
            dict(item, category=categories[item["categoryId"]])
            for item in products[offset : offset + PAGE_SIZE]
        ],
        "totalCount": len(products),
        "page": page,
        "pageSize": PAGE_SIZE,
        "pageCount": page_count,
        "activeChips": active_chips(criteria),
        "filterFeatures": filter_features(),
        "state": state,
    }


def filter_features() -> list[dict[str, str]]:
    features: dict[str, dict[str, str]] = {}
    for product in load_reference()["products"]:
        for feature in product.get("features", []):
            features.setdefault(feature["key"], {"key": feature["key"], "label": feature["label"]})
    return list(features.values())


def active_chips(criteria: CatalogueCriteria) -> list[dict[str, str]]:
    data = load_reference()
    chips: list[dict[str, str]] = []
    categories = {item["slug"]: item["name"] for item in data["categories"]}
    collections = {item["slug"]: item["name"] for item in data["collections"]}
    if criteria.category:
        chips.append({"key": "category", "value": criteria.category, "label": categories[criteria.category]})
    if criteria.collection:
        chips.append({"key": "collection", "value": criteria.collection, "label": collections[criteria.collection]})
    if criteria.price_min is not None:
        chips.append({"key": "priceMin", "value": str(criteria.price_min), "label": f"من {criteria.price_min} ج.م"})
    if criteria.price_max is not None:
        chips.append({"key": "priceMax", "value": str(criteria.price_max), "label": f"حتى {criteria.price_max} ج.م"})
    for feature in criteria.features:
        chips.append({"key": "feature", "value": feature, "label": feature})
    if criteria.availability:
        label = "متاح" if criteria.availability == "available" else "غير متاح"
        chips.append({"key": "availability", "value": criteria.availability, "label": label})
    return chips


def get_product(slug: str) -> dict[str, Any] | None:
    data = load_reference()
    return next((item for item in data["products"] if item["slug"] == slug), None)
