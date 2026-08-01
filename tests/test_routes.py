from django.test import SimpleTestCase
from django.urls import reverse


ROUTE_EXPECTATIONS = (
    {
        "label": "home",
        "name": "storefront:home",
        "status": 200,
        "template": "pages/home.html",
        "page_id": "home",
    },
    {
        "label": "shop",
        "name": "storefront:shop",
        "status": 200,
        "template": "pages/shop.html",
        "page_id": "shop",
    },
    {
        "label": "collection",
        "name": "storefront:collection",
        "kwargs": {"slug": "fingerprint-locks"},
        "status": 200,
        "template": "pages/shop.html",
        "page_id": "collection",
    },
    {
        "label": "search",
        "name": "storefront:search",
        "query": {"q": "ذكي"},
        "status": 200,
        "template": "pages/shop.html",
        "page_id": "search",
    },
    {
        "label": "product",
        "name": "storefront:product",
        "kwargs": {"slug": "zakey-apex-pro"},
        "status": 200,
        "template": "pages/product_detail.html",
        "page_id": "product",
    },
    {
        "label": "cart",
        "name": "storefront:cart",
        "status": 200,
        "template": "pages/cart.html",
        "page_id": "cart",
    },
    {
        "label": "checkout",
        "name": "storefront:checkout",
        "status": 200,
        "template": "pages/checkout.html",
        "page_id": "checkout",
    },
    {
        "label": "wishlist",
        "name": "storefront:wishlist",
        "status": 200,
        "template": "pages/wishlist.html",
        "page_id": "wishlist",
    },
    {
        "label": "account",
        "name": "storefront:account",
        "query": {"state": "signed-in"},
        "status": 200,
        "template": "pages/account.html",
        "page_id": "account",
    },
    {
        "label": "about",
        "name": "storefront:about",
        "status": 200,
        "template": "pages/about.html",
        "page_id": "about",
    },
    {
        "label": "contact",
        "name": "storefront:contact",
        "status": 200,
        "template": "pages/contact.html",
        "page_id": "contact",
    },
    {
        "label": "404 preview",
        "name": "storefront:error-404",
        "status": 404,
        "template": "pages/404.html",
        "page_id": "404",
    },
    {
        "label": "5xx preview",
        "name": "storefront:error-500",
        "status": 500,
        "template": "pages/500.html",
        "page_id": "5xx",
    },
)


class PresentationRouteTests(SimpleTestCase):
    def assert_shared_arabic_chrome(self, response, expected_page_id):
        document = response.content.decode("utf-8")
        self.assertIn('<html lang="ar-EG" dir="rtl">', document)
        self.assertIn('<body data-page="', document)
        self.assertIn("<header", document)
        self.assertIn("<main", document)
        self.assertIn("<footer", document)
        self.assertIn("تخطي إلى المحتوى", document)
        self.assertRegex(document, r"[\u0600-\u06ff]")
        self.assertEqual(response.context["page_id"], expected_page_id)

    def test_each_public_route_renders_its_page_in_the_shared_arabic_shell(self):
        for expected in ROUTE_EXPECTATIONS:
            with self.subTest(route=expected["label"]):
                url = reverse(expected["name"], kwargs=expected.get("kwargs"))
                response = self.client.get(url, expected.get("query", {}))
                self.assertEqual(response.status_code, expected["status"])
                self.assertTemplateUsed(response, expected["template"])
                self.assert_shared_arabic_chrome(response, expected["page_id"])

    def test_unknown_collection_and_product_use_the_shared_404_recovery_page(self):
        urls = {
            "collection": reverse(
                "storefront:collection",
                kwargs={"slug": "missing-collection"},
            ),
            "product": reverse(
                "storefront:product",
                kwargs={"slug": "missing-product"},
            ),
        }
        for resource, url in urls.items():
            with self.subTest(resource=resource):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404)
                self.assertTemplateUsed(response, "pages/404.html")
                self.assert_shared_arabic_chrome(response, "404")
