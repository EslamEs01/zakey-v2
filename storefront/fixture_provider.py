from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "frontend-fixtures.json"
ALLOWED_SORTS = {"featured", "price-asc", "price-desc", "name"}


class FixtureContractError(RuntimeError):
    """Raised when authored demonstration content violates the frontend contract."""


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
        raise FixtureContractError(f"Duplicate {label} {key}")


def _require_local_asset(path: str) -> None:
    if path.startswith(("http://", "https://", "//")):
        raise FixtureContractError(f"Remote asset is not allowed: {path}")


def _validate_fixture(data: dict[str, Any]) -> dict[str, Any]:
    required = {
        "meta",
        "site",
        "navigation",
        "categories",
        "collections",
        "products",
        "reviews",
        "faqs",
        "partners",
        "team",
        "governorates",
        "serviceEligibility",
        "shippingOptions",
        "paymentOptions",
        "prototypeAccounts",
        "prototypeCarts",
        "prototypeWishlists",
    }
    missing = sorted(required.difference(data))
    if missing:
        raise FixtureContractError(f"Missing fixture sections: {', '.join(missing)}")
    if data["meta"].get("fixtureStatus") != "demonstration":
        raise FixtureContractError("Fixture must be marked demonstration")

    for section in ("categories", "collections", "products", "reviews", "faqs"):
        _unique(data[section], "id", section)
    _unique(data["categories"], "slug", "categories")
    _unique(data["collections"], "slug", "collections")
    _unique(data["products"], "slug", "products")
    _unique(data["governorates"], "key", "governorates")
    if len(data["governorates"]) != 27:
        raise FixtureContractError("Fixture must contain exactly 27 governorates")

    category_ids = {item["id"] for item in data["categories"]}
    product_ids = {item["id"] for item in data["products"]}
    review_ids = {item["id"] for item in data["reviews"]}
    faq_ids = {item["id"] for item in data["faqs"]}
    for product in data["products"]:
        if product["categoryId"] not in category_ids:
            raise FixtureContractError(f"Unknown category for {product['id']}")
        if not 2190 <= int(product["price"]) <= 7490:
            raise FixtureContractError(f"Price outside prototype range for {product['id']}")
        for image in product.get("images", []):
            _require_local_asset(image["path"])
        if not set(product.get("reviewIds", [])).issubset(review_ids):
            raise FixtureContractError(f"Unknown review for {product['id']}")
        if not set(product.get("faqIds", [])).issubset(faq_ids):
            raise FixtureContractError(f"Unknown FAQ for {product['id']}")
        related = set(product.get("relatedProductIds", []))
        if product["id"] in related or not related.issubset(product_ids):
            raise FixtureContractError(f"Invalid related products for {product['id']}")

    for section in ("partners", "team"):
        for record in data[section]:
            asset = record.get("image") or record.get("mark")
            if asset:
                _require_local_asset(asset["path"] if isinstance(asset, dict) else asset)
    return data


@lru_cache(maxsize=1)
def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return _validate_fixture(json.load(fixture_file))


def _integer(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def normalize_criteria(query: Mapping[str, Any], collection: str | None = None) -> CatalogueCriteria:
    data = load_fixture()
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
    data = load_fixture()
    criteria = normalize_criteria(query, collection)
    products = list(data["products"])
    fixture_order = {product["id"]: index for index, product in enumerate(products)}
    categories = {item["id"]: item for item in data["categories"]}
    category_by_slug = {item["slug"]: item for item in data["categories"]}
    if criteria.collection:
        selected = next(item for item in data["collections"] if item["slug"] == criteria.collection)
        allowed = set(selected["productIds"])
        products = [product for product in products if product["id"] in allowed]
    if criteria.category:
        category_id = category_by_slug[criteria.category]["id"]
        products = [product for product in products if product["categoryId"] == category_id]
    if criteria.q:
        needle = criteria.q.casefold()
        products = [
            product
            for product in products
            if needle in " ".join(
                [product["name"], product.get("shortDescription", "")]
            ).casefold()
        ]
    if criteria.price_min is not None:
        products = [product for product in products if product["price"] >= criteria.price_min]
    if criteria.price_max is not None:
        products = [product for product in products if product["price"] <= criteria.price_max]
    if criteria.features:
        products = [
            product
            for product in products
            if set(criteria.features).issubset({item["key"] for item in product.get("features", [])})
        ]
    if criteria.availability == "available":
        products = [
            product
            for product in products
            if product["availability"] in {"available", "limited"}
        ]
    elif criteria.availability == "unavailable":
        products = [product for product in products if product["availability"] == "unavailable"]
    if criteria.sort == "price-asc":
        products.sort(key=lambda item: (item["price"], fixture_order[item["id"]]))
    elif criteria.sort == "price-desc":
        products.sort(key=lambda item: (-item["price"], fixture_order[item["id"]]))
    elif criteria.sort == "name":
        products.sort(key=lambda item: (item["name"], fixture_order[item["id"]]))
    else:
        products.sort(key=lambda item: fixture_order[item["id"]])

    page_size = 6
    page_count = max(1, (len(products) + page_size - 1) // page_size)
    page = min(criteria.page, page_count)
    offset = (page - 1) * page_size
    q = criteria.q
    has_filters = any(
        [criteria.category, criteria.collection, criteria.price_min, criteria.price_max,
         criteria.features, criteria.availability]
    )
    state = "populated"
    if not products:
        state = "no-search-results" if q and not has_filters else "no-filtered-results"
    return {
        "criteria": criteria,
        "products": [dict(item, category=categories[item["categoryId"]]) for item in products[offset:offset + page_size]],
        "totalCount": len(products),
        "page": page,
        "pageSize": page_size,
        "pageCount": page_count,
        "activeChips": _active_chips(criteria, data),
        "filterFeatures": _filter_features(data),
        "state": state,
    }


def _filter_features(data: dict[str, Any]) -> list[dict[str, str]]:
    features: dict[str, dict[str, str]] = {}
    for product in data["products"]:
        for feature in product.get("features", []):
            features.setdefault(feature["key"], {"key": feature["key"], "label": feature["label"]})
    return list(features.values())


def _active_chips(criteria: CatalogueCriteria, data: dict[str, Any]) -> list[dict[str, str]]:
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
    data = load_fixture()
    product = next((item for item in data["products"] if item["slug"] == slug), None)
    if product is None:
        return None
    related_ids = product.get("relatedProductIds", [])
    related = [item for item in data["products"] if item["id"] in related_ids]
    reviews = [item for item in data["reviews"] if item["id"] in product.get("reviewIds", [])]
    faqs = [item for item in data["faqs"] if item["id"] in product.get("faqIds", [])]
    return {
        "product": product,
        "relatedProducts": related,
        "reviews": reviews,
        "faqs": faqs,
        "selectedImageId": product["images"][0]["id"],
        "selectedFinishId": product["finishes"][0]["id"],
        "prototypeNotice": data["site"]["prototypeNotice"],
    }


def get_site_context() -> dict[str, Any]:
    data = load_fixture()
    return {
        "site": data["site"],
        "navigation": data["navigation"],
        "categories": data["categories"],
        "collections": data["collections"],
        "client_fixture": get_client_fixture(),
    }


def get_client_fixture() -> dict[str, Any]:
    data = load_fixture()
    keys = (
        "meta", "site", "categories", "collections", "products", "reviews", "faqs",
        "governorates", "serviceEligibility", "shippingOptions", "paymentOptions",
        "prototypeAccounts", "prototypeCarts", "prototypeWishlists",
    )
    return deepcopy({key: data[key] for key in keys})


def page_context(page: str, state: str = "default") -> dict[str, Any]:
    data = load_fixture()
    context = get_site_context()
    context.update({"page_id": page, "page_state": state, "fixture": data})
    return context
