"""Integrity of the approved reference dataset and its oracle (T-1608).

The oracle is what ``test_catalogue_parity`` measures the database against, so
if the oracle drifts the parity proof silently becomes meaningless. These tests
pin the dataset's shape and the oracle's query behaviour — the same assertions
that used to guard ``storefront/fixture_provider.py`` when it served requests.

Nothing here touches the database. This is the frozen record of the approved
prototype, not a description of the running system.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import QueryDict
from django.test import SimpleTestCase

from tests.fixtures.reference_catalogue import (
    filter_features,
    get_catalogue,
    load_reference,
)

CANONICAL_GOVERNORATE_KEYS = {
    "alexandria", "aswan", "asyut", "beheira", "beni-suef", "cairo", "dakahlia",
    "damietta", "faiyum", "gharbia", "giza", "ismailia", "kafr-el-sheikh", "luxor",
    "matrouh", "minya", "monufia", "new-valley", "north-sinai", "port-said",
    "qalyubia", "qena", "red-sea", "sharqia", "sohag", "south-sinai", "suez",
}


class ReferenceDatasetTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = load_reference()

    def test_dataset_is_demonstration_data(self):
        self.assertEqual(self.data["meta"]["fixtureStatus"], "demonstration")

    def test_dataset_contains_each_canonical_governorate_once(self):
        keys = [item["key"] for item in self.data["governorates"]]
        self.assertEqual(len(keys), 27)
        self.assertEqual(set(keys), CANONICAL_GOVERNORATE_KEYS)

    def test_product_prices_stay_within_the_approved_range(self):
        for product in self.data["products"]:
            with self.subTest(product=product["slug"]):
                self.assertGreaterEqual(product["price"], 2190)
                self.assertLessEqual(product["price"], 7490)

    def test_authored_asset_paths_are_local_and_resolve_to_files(self):
        for product in self.data["products"]:
            for image in product["images"]:
                with self.subTest(asset=image["path"]):
                    self.assertTrue(image["path"].startswith("/static/"), image["path"])
                    local = Path(settings.BASE_DIR, image["path"].removeprefix("/"))
                    self.assertTrue(local.is_file(), image["path"])

    def test_the_frozen_counts_are_unchanged(self):
        self.assertEqual(len(self.data["products"]), 9)
        self.assertEqual(len(self.data["collections"]), 6)
        self.assertEqual(len(self.data["categories"]), 4)


class ReferenceCatalogueBehaviourTests(SimpleTestCase):
    """The query semantics the database implementation must reproduce."""

    def test_arabic_search_returns_the_matching_product(self):
        catalogue = get_catalogue({"q": "  أبيكس  "})
        self.assertEqual(catalogue["state"], "populated")
        self.assertIn("zakey-apex-pro", [p["slug"] for p in catalogue["products"]])

    def test_repeated_feature_and_price_filters_intersect(self):
        query = QueryDict("category=fingerprint&priceMax=5000&feature=fingerprint&feature=pin")
        catalogue = get_catalogue(query)
        for product in catalogue["products"]:
            keys = {feature["key"] for feature in product["features"]}
            self.assertTrue({"fingerprint", "pin"}.issubset(keys))
            self.assertLessEqual(product["price"], 5000)

    def test_price_sorting_orders_both_directions(self):
        ascending = [p["price"] for p in get_catalogue({"sort": "price-asc"})["products"]]
        descending = [p["price"] for p in get_catalogue({"sort": "price-desc"})["products"]]
        self.assertEqual(ascending, sorted(ascending))
        self.assertEqual(descending, sorted(descending, reverse=True))

    def test_out_of_range_page_clamps_to_the_last_populated_page(self):
        catalogue = get_catalogue({"page": "99"})
        self.assertEqual(catalogue["page"], catalogue["pageCount"])
        self.assertTrue(catalogue["products"])

    def test_search_and_filter_empty_results_stay_distinguishable(self):
        self.assertEqual(get_catalogue({"q": "no-such-product"})["state"], "no-search-results")
        self.assertEqual(
            get_catalogue({"category": "fingerprint", "priceMax": "1"})["state"],
            "no-filtered-results",
        )

    def test_available_filter_includes_limited_stock_products(self):
        """The approved semantics: 'available' matches available AND limited."""
        available = get_catalogue({"availability": "available"})["products"]
        states = {product["availability"] for product in available}
        self.assertTrue(states.issubset({"available", "limited"}))
        self.assertNotIn("unavailable", states)

    def test_unavailable_filter_excludes_available_and_limited(self):
        products = get_catalogue({"availability": "unavailable"})["products"]
        for product in products:
            self.assertEqual(product["availability"], "unavailable")

    def test_page_size_is_six(self):
        self.assertEqual(get_catalogue({})["pageSize"], 6)
        self.assertLessEqual(len(get_catalogue({})["products"]), 6)

    def test_filter_features_are_distinct_and_labelled(self):
        features = filter_features()
        keys = [feature["key"] for feature in features]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(all(feature["label"] for feature in features))
