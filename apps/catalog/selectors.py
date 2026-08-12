"""Catalogue read selectors (FR-130, NFR-002).

These mirror the approved ``storefront.fixture_provider.get_catalogue`` exactly:
same published list, same filter / sort / search / pagination semantics — page
size 6 with the out-of-range page clamped after filtering — and the same result
contract keys. The fixture provider is **not** imported here; the behaviour is
derived from the same rules against the catalogue models.

Selectors are read-only: they never write. ``get_catalogue`` issues a bounded,
asserted query count with no N+1 across products, categories, images, variants
or features (NFR-002).
"""

from __future__ import annotations

from dataclasses import dataclass

from django.utils.translation import gettext as _

from apps.core.i18n import translated as tr
from apps.core.models import PublicationStatus

from .models import (
    Availability,
    Category,
    Collection,
    CollectionProduct,
    Product,
    ProductFeature,
)

ALLOWED_SORTS: frozenset[str] = frozenset({"featured", "price-asc", "price-desc", "name"})
PAGE_SIZE = 6


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


def _integer(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def published_products():
    """Published catalogue products with all list data, ordered by ``position``.

    The featured/fixture order is governed catalogue ``position`` (with ``id``
    as the final tie-break, mirroring ``Product.Meta.ordering``); every sort in
    ``get_catalogue`` re-ties on that same order so it stays stable.
    """
    return (
        Product.objects.filter(status=PublicationStatus.PUBLISHED)
        .select_related("category")
        .prefetch_related(
            "images",
            "variants__stock_item",
            "features",
            "collectionproduct_set__collection",
        )
    )


def published_list():
    """Alias used by list views (FR-013): published storefront products."""
    return published_products()


def _feature_keys() -> set[str]:
    """Feature keys present across published products (facet universe)."""
    return set(
        ProductFeature.objects.filter(product__status=PublicationStatus.PUBLISHED)
        .values_list("key", flat=True)
        .distinct()
    )


def normalize_criteria(query, collection: str | None = None) -> CatalogueCriteria:
    """Coerce a raw query mapping into validated catalogue criteria.

    Mirrors ``fixture_provider.normalize_criteria``: unknown slugs, features and
    sorts are discarded; page is floored at 1; reversed price bounds swap back;
    price values are clamped at 0.
    """
    category_slugs = set(
        Category.objects.filter(status=PublicationStatus.PUBLISHED).values_list(
            "slug", flat=True
        )
    )
    collection_slugs = set(
        Collection.objects.filter(status=PublicationStatus.PUBLISHED).values_list(
            "slug", flat=True
        )
    )
    feature_values = _feature_keys()

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
        availability=availability
        if availability in {Availability.AVAILABLE, Availability.UNAVAILABLE}
        else None,
        sort=sort if sort in ALLOWED_SORTS else "featured",
        page=page,
    )


def _price_sort_key(product: Product) -> float:
    """Numeric VAT-inclusive display price used for price comparisons/sorts."""
    price = product.display_price
    return float(price) if price is not None else 0.0


def _catalogue_product(product: Product) -> dict:
    """Map a (prefetched) product onto the storefront's camelCase shape.

    Keys mirror the fixture product record exactly (frontend-contract.md §3) so
    the rendered catalogue card is unchanged (FR-130). Ordering-sensitive lists
    (images, finishes, features, collection ids) follow each model's explicit
    ``position`` ordering.
    """
    images = list(product.images.all())
    variants = list(product.variants.all())
    features = list(product.features.all())
    memberships = list(product.collectionproduct_set.all())

    default_variant = next((v for v in variants if v.is_default), None) or next(
        iter(variants), None
    )

    return {
        # `id` stays the legacy string the storefront markup keys on; `pk` and
        # `defaultVariantId` are the real database keys the mutation forms post,
        # so a form never has to round-trip through a display identifier.
        "id": product.legacy_id or product.slug,
        "pk": product.pk,
        "defaultVariantId": default_variant.pk if default_variant else None,
        "slug": product.slug,
        "name": tr(product, "name"),
        "shortDescription": tr(product, "short_description"),
        "categoryId": product.category.legacy_id or product.category.slug,
        "collectionIds": [
            m.collection.legacy_id or m.collection.slug for m in memberships
        ],
        "price": product.display_price,
        "compareAtPrice": product.compare_at_price,
        # `or None`: a blank CharField and "no badge" are the same thing to the
        # storefront, and the approved contract spells that absence as null.
        "badge": tr(product, "badge") or None,
        "rating": product.rating_average,
        "reviewCount": product.review_count,
        "availability": product.availability,
        "images": [
            {
                "id": img.legacy_id or str(img.id),
                "path": img.src,
                "width": img.width,
                "height": img.height,
                "alt": tr(img, "alt"),
            }
            for img in images
        ],
        "finishes": [
            {
                "id": v.finish_id or v.sku,
                # The finish radio posts this, so choosing a finish selects the
                # exact variant row the cart line will be keyed on.
                "variantId": v.pk,
                "label": tr(v, "finish_label"),
                "swatch": v.swatch_hex,
                "available": bool(
                    getattr(v, "stock_item", None) and v.stock_item.available > 0
                ),
            }
            for v in variants
        ],
        "features": [
            {"key": f.key, "label": tr(f, "label"), "description": tr(f, "description")}
            for f in features
        ],
        "instalmentMessage": tr(product, "instalment_message"),
        "serviceFlags": {
            "sameDaySupported": product.same_day_supported,
            "installationSupported": product.installation_supported,
        },
        "category": {
            "id": product.category.legacy_id or product.category.slug,
            "slug": product.category.slug,
            "name": tr(product.category, "name"),
            "description": tr(product.category, "description"),
            "kind": tr(product.category, "kind"),
        },
    }


def get_catalogue(query, collection: str | None = None) -> dict:
    """Filter, sort, search and paginate the published catalogue.

    Output is identical to ``fixture_provider.get_catalogue`` for the canonical
    cases: AND-semantics feature facets, all four sorts with a stable
    tie-break, case-folded name/description search, and page size exactly 6 with
    the page clamped after filtering (FR-130, NFR-002).
    """
    criteria = normalize_criteria(query, collection)
    products = list(published_products())
    featured_order = {p.pk: index for index, p in enumerate(products)}

    if criteria.collection:
        selected = Collection.objects.get(
            slug=criteria.collection, status=PublicationStatus.PUBLISHED
        )
        allowed_ids = set(
            CollectionProduct.objects.filter(collection=selected).values_list(
                "product_id", flat=True
            )
        )
        products = [p for p in products if p.pk in allowed_ids]
    if criteria.category:
        category = Category.objects.get(
            slug=criteria.category, status=PublicationStatus.PUBLISHED
        )
        products = [p for p in products if p.category_id == category.pk]
    if criteria.q:
        needle = criteria.q.casefold()
        # Searched in whichever language the visitor is reading, and in Arabic
        # too: an English speaker typing a product's Arabic name still finds it.
        products = [
            p
            for p in products
            if needle
            in " ".join(
                [
                    p.name,
                    p.short_description or "",
                    p.name_en or "",
                    p.short_description_en or "",
                ]
            ).casefold()
        ]
    if criteria.price_min is not None:
        products = [p for p in products if _price_sort_key(p) >= criteria.price_min]
    if criteria.price_max is not None:
        products = [p for p in products if _price_sort_key(p) <= criteria.price_max]
    if criteria.features:
        wanted = set(criteria.features)
        products = [
            p
            for p in products
            if wanted.issubset({f.key for f in p.features.all()})
        ]
    if criteria.availability == Availability.AVAILABLE:
        products = [
            p
            for p in products
            if p.availability in {Availability.AVAILABLE, Availability.LIMITED}
        ]
    elif criteria.availability == Availability.UNAVAILABLE:
        products = [p for p in products if p.availability == Availability.UNAVAILABLE]

    if criteria.sort == "price-asc":
        products.sort(key=lambda p: (_price_sort_key(p), featured_order[p.pk]))
    elif criteria.sort == "price-desc":
        products.sort(key=lambda p: (-_price_sort_key(p), featured_order[p.pk]))
    elif criteria.sort == "name":
        products.sort(key=lambda p: (tr(p, "name"), featured_order[p.pk]))
    else:  # featured
        products.sort(key=lambda p: featured_order[p.pk])

    page_count = max(1, (len(products) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(criteria.page, page_count)
    offset = (page - 1) * PAGE_SIZE
    has_filters = any(
        [
            criteria.category,
            criteria.collection,
            criteria.price_min,
            criteria.price_max,
            criteria.features,
            criteria.availability,
        ]
    )
    state = "populated"
    if not products:
        state = (
            "no-search-results"
            if criteria.q and not has_filters
            else "no-filtered-results"
        )

    page_products = products[offset : offset + PAGE_SIZE]
    return {
        "criteria": criteria,
        "products": [_catalogue_product(p) for p in page_products],
        "totalCount": len(products),
        "page": page,
        "pageSize": PAGE_SIZE,
        "pageCount": page_count,
        "activeChips": _active_chips(criteria),
        "filterFeatures": _filter_features(),
        "state": state,
    }


def _filter_features() -> list[dict[str, str]]:
    """Distinct feature keys/labels across published products, stable order."""
    seen: dict[str, str] = {}
    features = ProductFeature.objects.filter(
        product__status=PublicationStatus.PUBLISHED
    ).order_by("product__position", "position", "id")
    for feature in features:
        seen.setdefault(feature.key, tr(feature, "label"))
    return [{"key": key, "label": label} for key, label in seen.items()]


def _active_chips(criteria: CatalogueCriteria) -> list[dict[str, str]]:
    chips: list[dict[str, str]] = []
    if criteria.category:
        category = Category.objects.get(slug=criteria.category)
        chips.append(
            {"key": "category", "value": criteria.category, "label": tr(category, "name")}
        )
    if criteria.collection:
        collection = Collection.objects.get(slug=criteria.collection)
        chips.append(
            {
                "key": "collection",
                "value": criteria.collection,
                "label": tr(collection, "name"),
            }
        )
    if criteria.price_min is not None:
        chips.append(
            {
                "key": "priceMin",
                "value": str(criteria.price_min),
                "label": _("من %(amount)s ج.م") % {"amount": criteria.price_min},
            }
        )
    if criteria.price_max is not None:
        chips.append(
            {
                "key": "priceMax",
                "value": str(criteria.price_max),
                "label": _("حتى %(amount)s ج.م") % {"amount": criteria.price_max},
            }
        )
    for feature in criteria.features:
        chips.append({"key": "feature", "value": feature, "label": feature})
    if criteria.availability:
        label = (
            _("متاح") if criteria.availability == "available" else _("غير متاح")
        )
        chips.append({"key": "availability", "value": criteria.availability, "label": label})
    return chips


# ---------------------------------------------------------------------------
# Product detail (T-1603, FR-130)
# ---------------------------------------------------------------------------


def _detail_product(product: Product) -> dict:
    """The catalogue card record plus everything only the detail page renders.

    Built on top of :func:`_catalogue_product` so a product looks identical
    whether it is rendered as a card or as a detail page — the card fields have
    exactly one definition.
    """
    record = _catalogue_product(product)
    record["specificationGroups"] = [
        {
            "id": group.legacy_id or str(group.pk),
            "label": tr(group, "label"),
            "items": [
                {"label": tr(item, "label"), "value": tr(item, "value")}
                for item in group.items.all()
            ],
        }
        for group in product.specification_groups.all()
    ]
    record["downloads"] = [
        {
            "id": document.legacy_id or str(document.pk),
            "label": tr(document, "label"),
            "path": document.src,
            "format": document.file_format,
            # Kept for template compatibility; staff can clear it per document.
            "prototypeNotice": tr(document, "notice"),
        }
        for document in product.documents.all()
    ]
    return record


def _review_record(review) -> dict:
    return {
        "id": review.legacy_id or str(review.pk),
        # Falls back to the language it was written in, which is the right
        # default for customer-authored text: a review is only ever shown in
        # English when a staff member has actually supplied that English.
        "customerName": tr(review, "author_name"),
        "rating": review.rating,
        "quote": tr(review, "body"),
        "prototypeAttribution": tr(review, "title"),
        "isVerifiedPurchase": review.is_verified_purchase,
        "placement": review.placement or [],
    }


def get_product_detail(slug: str) -> dict | None:
    """Everything the product page renders, or ``None`` when there is no
    published product at ``slug`` (the view turns that into the 404 page).

    Replaces ``fixture_provider.get_product`` with the same result keys.
    Unpublished and archived products are invisible here exactly as they are in
    the catalogue list (FR-013), so a direct URL cannot reveal a draft.
    """
    from apps.content.models import FAQ
    from apps.reviews.models import Review

    product = (
        published_products()
        .prefetch_related(
            "specification_groups__items",
            "documents",
            "relations_from__to_product__images",
            "relations_from__to_product__category",
            "relations_from__to_product__variants__stock_item",
            "relations_from__to_product__features",
            "relations_from__to_product__collectionproduct_set__collection",
        )
        .filter(slug=slug)
        .first()
    )
    if product is None:
        return None

    related = [
        relation.to_product
        for relation in product.relations_from.all()
        if relation.to_product.status == PublicationStatus.PUBLISHED
    ]
    reviews = Review.objects.approved().filter(product=product)
    faqs = FAQ.objects.filter(is_active=True, products=product)

    record = _detail_product(product)
    return {
        "product": record,
        "relatedProducts": [_catalogue_product(item) for item in related],
        "reviews": [_review_record(review) for review in reviews],
        "faqs": [
            {
                "id": faq.legacy_id or str(faq.pk),
                "question": tr(faq, "question"),
                "answer": tr(faq, "answer"),
            }
            for faq in faqs
        ],
        "selectedImageId": record["images"][0]["id"] if record["images"] else None,
        "selectedFinishId": record["finishes"][0]["id"] if record["finishes"] else None,
    }
