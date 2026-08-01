from importlib.util import find_spec
from pathlib import Path

from django.conf import settings
from django.http import QueryDict
from django.test import SimpleTestCase

import storefront
from storefront.fixture_provider import get_catalogue, get_client_fixture, load_fixture


CANONICAL_GOVERNORATE_KEYS = {
    "alexandria",
    "aswan",
    "asyut",
    "beheira",
    "beni-suef",
    "cairo",
    "dakahlia",
    "damietta",
    "faiyum",
    "gharbia",
    "giza",
    "ismailia",
    "kafr-el-sheikh",
    "luxor",
    "matrouh",
    "minya",
    "monufia",
    "new-valley",
    "north-sinai",
    "port-said",
    "qalyubia",
    "qena",
    "red-sea",
    "sharqia",
    "sohag",
    "south-sinai",
    "suez",
}

REQUIRED_FIXTURE_SECTIONS = {
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


def fixture_asset_paths(content):
    if isinstance(content, dict):
        if isinstance(content.get("path"), str):
            yield content["path"]
        for nested_content in content.values():
            yield from fixture_asset_paths(nested_content)
    elif isinstance(content, list):
        for nested_content in content:
            yield from fixture_asset_paths(nested_content)


class FixtureContractTests(SimpleTestCase):
    def setUp(self):
        self.fixture = load_fixture()

    def test_fixture_is_demonstration_data_with_one_complete_root(self):
        self.assertEqual(self.fixture["meta"]["fixtureStatus"], "demonstration")
        self.assertTrue(REQUIRED_FIXTURE_SECTIONS.issubset(self.fixture))
        self.assertEqual(self.fixture["site"]["locale"], "ar-EG")
        self.assertEqual(self.fixture["site"]["direction"], "rtl")
        self.assertEqual(self.fixture["site"]["currency"]["label"], "ج.م")
        self.assertEqual(self.fixture["site"]["vatRate"], 0.14)
        self.assertEqual(self.fixture["site"]["freeShippingThreshold"], 1500)

    def test_fixture_contains_each_canonical_governorate_once(self):
        governorate_keys = [entry["key"] for entry in self.fixture["governorates"]]
        self.assertEqual(len(governorate_keys), 27)
        self.assertEqual(set(governorate_keys), CANONICAL_GOVERNORATE_KEYS)
        self.assertEqual(len(governorate_keys), len(set(governorate_keys)))
        self.assertEqual(
            set(self.fixture["serviceEligibility"]["installationGovernorateKeys"]),
            {"cairo", "giza", "alexandria"},
        )

    def test_product_prices_stay_within_the_egyptian_prototype_range(self):
        products = self.fixture["products"]
        self.assertEqual(len(products), 9)
        for product in products:
            with self.subTest(product=product["slug"]):
                self.assertIs(type(product["price"]), int)
                self.assertGreaterEqual(product["price"], 2190)
                self.assertLessEqual(product["price"], 7490)

    def test_authored_asset_paths_are_local_and_resolve_to_files(self):
        asset_paths = sorted(set(fixture_asset_paths(self.fixture)))
        self.assertTrue(asset_paths)
        for asset_path in asset_paths:
            with self.subTest(asset=asset_path):
                self.assertTrue(asset_path.startswith("/static/"), asset_path)
                local_path = Path(settings.BASE_DIR, asset_path.removeprefix("/"))
                self.assertTrue(local_path.is_file(), asset_path)

    def test_client_fixture_mutation_cannot_change_authored_defaults(self):
        client_fixture = get_client_fixture()
        original_price = client_fixture["products"][0]["price"]
        client_fixture["products"][0]["price"] = 0
        self.assertEqual(get_client_fixture()["products"][0]["price"], original_price)


class CatalogueBehaviorTests(SimpleTestCase):
    def test_arabic_search_returns_the_matching_product(self):
        catalogue = get_catalogue({"q": "  أبيكس  "})
        self.assertEqual(catalogue["state"], "populated")
        self.assertEqual(catalogue["totalCount"], 1)
        self.assertEqual(
            [product["slug"] for product in catalogue["products"]],
            ["zakey-apex-pro"],
        )

    def test_repeated_feature_and_price_filters_intersect_results(self):
        query = QueryDict("category=fingerprint&priceMax=5000&feature=fingerprint&feature=pin")
        catalogue = get_catalogue(query)
        self.assertEqual(
            [product["slug"] for product in catalogue["products"]],
            ["zakey-nova-s2"],
        )
        self.assertEqual(
            [(chip["key"], chip["value"]) for chip in catalogue["activeChips"]],
            [
                ("category", "fingerprint"),
                ("priceMax", "5000"),
                ("feature", "fingerprint"),
                ("feature", "pin"),
            ],
        )

    def test_price_sorting_orders_the_first_page_in_both_directions(self):
        expected_orders = {
            "price-asc": [
                "zakey-bridge-mini",
                "zakey-guard-view",
                "zakey-core-c1",
                "zakey-nova-s2",
                "zakey-orbit-k3",
                "zakey-pulse-f5",
            ],
            "price-desc": [
                "zakey-apex-pro",
                "zakey-nexus-elite",
                "zakey-vision-x",
                "zakey-pulse-f5",
                "zakey-orbit-k3",
                "zakey-nova-s2",
            ],
        }
        for sort, expected_slugs in expected_orders.items():
            with self.subTest(sort=sort):
                catalogue = get_catalogue({"sort": sort})
                self.assertEqual(
                    [product["slug"] for product in catalogue["products"]],
                    expected_slugs,
                )

    def test_out_of_range_page_clamps_to_the_last_populated_page(self):
        catalogue = get_catalogue({"page": "99"})
        self.assertEqual(catalogue["page"], 2)
        self.assertEqual(catalogue["pageCount"], 2)
        self.assertEqual(
            [product["slug"] for product in catalogue["products"]],
            ["zakey-core-c1", "zakey-guard-view", "zakey-bridge-mini"],
        )

    def test_search_and_filter_empty_results_remain_distinguishable(self):
        scenarios = {
            "search": ({"q": "لايوجدمنتج"}, "no-search-results"),
            "filters": (
                {"category": "accessories", "priceMax": "2189"},
                "no-filtered-results",
            ),
        }
        for scenario, (query, expected_state) in scenarios.items():
            with self.subTest(scenario=scenario):
                catalogue = get_catalogue(query)
                self.assertEqual(catalogue["products"], [])
                self.assertEqual(catalogue["totalCount"], 0)
                self.assertEqual(catalogue["state"], expected_state)

    def test_unavailable_filter_excludes_available_and_limited_products(self):
        catalogue = get_catalogue({"availability": "unavailable"})
        self.assertEqual(
            [product["slug"] for product in catalogue["products"]],
            ["zakey-core-c1"],
        )


class FrontendBoundaryTests(SimpleTestCase):
    def test_django_shell_has_no_database_or_business_application_dependencies(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.dummy",
        )
        self.assertEqual(settings.DATABASES["default"]["NAME"], "")
        prohibited_apps = {
            "django.contrib.admin",
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
        }
        self.assertTrue(prohibited_apps.isdisjoint(settings.INSTALLED_APPS))
        self.assertNotIn(
            "django.contrib.sessions.middleware.SessionMiddleware",
            settings.MIDDLEWARE,
        )
        self.assertIsNone(find_spec("storefront.models"))
        self.assertIsNone(find_spec("storefront.admin"))
        storefront_path = Path(storefront.__file__).parent
        self.assertFalse((storefront_path / "migrations").exists())
