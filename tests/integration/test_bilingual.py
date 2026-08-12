"""Arabic/English bilingual behaviour (FR-136).

Three separate mechanisms have to agree for the storefront to be genuinely
bilingual, and each one fails silently on its own:

* **gettext** translates the templates. A missing catalogue entry renders the
  Arabic msgid, which looks fine on an Arabic page and wrong on an English one.
* **``_en`` model columns** translate the catalogue. An empty column falls back
  to Arabic — deliberately — so an untranslated product also renders without
  erroring.
* **``dir`` on ``<html>``** mirrors the layout. Get it wrong and every page is
  still readable, just laid out backwards.

None of those raise. All of them are asserted here.
"""

from __future__ import annotations

import re

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import translation

pytestmark = pytest.mark.django_db

ARABIC = re.compile(r"[؀-ۿ]")

#: Every public page, so a language regression cannot hide on one route.
PAGES = [
    "storefront:home", "storefront:shop", "storefront:cart", "storefront:checkout",
    "storefront:wishlist", "storefront:account", "storefront:about", "storefront:contact",
]


def visible_text(html: str) -> list[str]:
    """Rendered text, minus scripts and the switcher's own language names."""
    body = re.sub(r"(?s)<(script|style|noscript)\b.*?</\1>", " ", html)
    body = re.sub(r'(?s)<form class="language-switcher".*?</form>', " ", body)
    body = re.sub(r"(?s)<[^>]+>", "\n", body)
    return [re.sub(r"\s+", " ", line).strip() for line in body.split("\n") if line.strip()]


def switch(client: Client, language: str) -> None:
    response = client.post(
        reverse("storefront:set-language"), {"language": language, "next": "/"}
    )
    assert response.status_code == 302


class TestTheSwitcher:
    def test_it_is_on_every_page(self, storefront):
        for name in PAGES:
            html = storefront.get(reverse(name)).content.decode()
            assert "language-switcher" in html, f"{name} has no language switcher"
            assert "icon-globe" in html, f"{name} switcher has no icon"

    def test_it_sets_a_cookie_and_changes_the_language(self, storefront):
        from django.conf import settings

        switch(storefront, "en")

        assert storefront.cookies[settings.LANGUAGE_COOKIE_NAME].value == "en"
        html = storefront.get(reverse("storefront:home")).content.decode()
        assert 'lang="en' in html

    def test_it_returns_to_the_page_it_was_used_on(self, storefront):
        response = storefront.post(
            reverse("storefront:set-language"),
            {"language": "en", "next": reverse("storefront:contact")},
        )

        assert response.headers["Location"] == reverse("storefront:contact")

    def test_it_refuses_a_get(self, storefront):
        """A language switch writes a cookie, so it must not be reachable by a
        prefetching browser or a crawler following a link."""
        assert storefront.get(reverse("storefront:set-language")).status_code == 405

    def test_it_refuses_an_offsite_redirect(self, storefront):
        response = storefront.post(
            reverse("storefront:set-language"),
            {"language": "en", "next": "https://evil.example/steal"},
        )

        assert response.headers["Location"] == reverse("storefront:home")

    def test_an_unknown_language_falls_back_to_the_default(self, storefront):
        from django.conf import settings

        switch(storefront, "en")
        storefront.post(
            reverse("storefront:set-language"), {"language": "de", "next": "/"}
        )

        assert (
            storefront.cookies[settings.LANGUAGE_COOKIE_NAME].value
            == settings.LANGUAGE_CODE
        )


class TestDirection:
    """The page has to mirror, not merely translate."""

    @pytest.mark.parametrize(
        ("language", "direction"), [("ar", "rtl"), ("en", "ltr")]
    )
    def test_every_page_carries_the_right_direction(
        self, storefront, language, direction
    ):
        switch(storefront, language)

        for name in PAGES:
            html = storefront.get(reverse(name)).content.decode()
            match = re.search(r"<html[^>]*>", html)
            assert f'dir="{direction}"' in match.group(0), (
                f"{name} in {language} rendered {match.group(0)}"
            )

    def test_the_error_pages_mirror_too(self, storefront):
        """404 and 500 render from their own views, so they are asserted
        separately — an unmirrored error page is exactly the one nobody looks
        at until a customer hits it."""
        switch(storefront, "en")

        for name in ("storefront:error-404", "storefront:error-500"):
            html = storefront.get(reverse(name)).content.decode()
            assert 'dir="ltr"' in re.search(r"<html[^>]*>", html).group(0)


class TestTemplateCopyIsTranslated:
    #: Arabic template strings and the English they must become. Asserted as
    #: pairs rather than "no Arabic anywhere", because catalogue *data* seeded
    #: Arabic-only is supposed to fall back to Arabic on an English page.
    PAIRS = [
        ("storefront:cart", "سلة التسوق", "Cart"),
        ("storefront:cart", "سلتك فارغة حاليًا", "Your cart is empty"),
        ("storefront:wishlist", "قائمة المفضلة", "Wishlist"),
        ("storefront:account", "تسجيل الدخول", "Sign in"),
        ("storefront:checkout", "إتمام الطلب", "Checkout"),
        ("storefront:contact", "كيف يمكننا مساعدتك؟", "How can we help?"),
    ]

    @pytest.mark.parametrize(("route", "arabic", "english"), PAIRS)
    def test_template_copy_becomes_english(self, storefront, route, arabic, english):
        switch(storefront, "en")

        html = storefront.get(reverse(route)).content.decode()

        assert english in html, f"{route} never rendered {english!r}"
        assert arabic not in html, f"{route} still renders the Arabic {arabic!r}"

    def test_the_page_chrome_carries_no_arabic_in_english(self, storefront):
        """The header, footer and cart page own no catalogue data beyond the
        category menu, so everything else on them is template copy."""
        switch(storefront, "en")
        lines = visible_text(storefront.get(reverse("storefront:cart")).content.decode())

        from apps.catalog.models import Category

        category_names = {c.name for c in Category.objects.all()}
        arabic = [
            line for line in lines
            if ARABIC.search(line) and line not in category_names
        ]

        assert not arabic, f"untranslated template copy: {arabic[:5]}"

    def test_arabic_is_unaffected(self, storefront):
        """The i18n markup must be a no-op in the source language."""
        switch(storefront, "ar")
        html = storefront.get(reverse("storefront:cart")).content.decode()

        assert "سلة التسوق" in html
        assert 'dir="rtl"' in html


class TestModelTranslation:
    def test_english_copy_is_served_when_present(self, product, variant):
        from apps.catalog.selectors import get_product_detail

        product.name_en = "ZAKEY Apex Pro"
        product.short_description_en = "A premium main-door lock."
        product.save(update_fields=["name_en", "short_description_en"])

        with translation.override("en"):
            record = get_product_detail(product.slug)

        assert record["product"]["name"] == "ZAKEY Apex Pro"
        assert record["product"]["shortDescription"] == "A premium main-door lock."

    def test_it_falls_back_per_field_not_per_record(self, product, variant):
        """A product with an English name but no English description must read
        correctly in both halves, not blank out the untranslated one."""
        from apps.catalog.selectors import get_product_detail

        product.name_en = "ZAKEY Apex Pro"
        product.short_description_en = ""
        product.save(update_fields=["name_en", "short_description_en"])

        with translation.override("en"):
            record = get_product_detail(product.slug)

        assert record["product"]["name"] == "ZAKEY Apex Pro"
        assert record["product"]["shortDescription"] == product.short_description

    def test_arabic_never_reads_the_english_column(self, product, variant):
        from apps.catalog.selectors import get_product_detail

        product.name_en = "ZAKEY Apex Pro"
        product.save(update_fields=["name_en"])

        with translation.override("ar"):
            record = get_product_detail(product.slug)

        assert record["product"]["name"] == product.name

    def test_search_matches_either_language(self, product, variant):
        from apps.catalog.selectors import get_catalogue

        product.name_en = "Apex Pro fingerprint lock"
        product.save(update_fields=["name_en"])

        with translation.override("en"):
            results = get_catalogue({"q": "fingerprint"})

        assert any(item["slug"] == product.slug for item in results["products"])

    def test_translation_complete_reports_missing_english(self, product):
        assert product.translation_complete is False

        for field in product.translatable_fields:
            setattr(product, f"{field}_en", "x")

        assert product.translation_complete is True


class TestPageCopyOverlay:
    def test_english_overlays_merge_over_the_arabic_structure(self, db):
        """A sparse overlay must not blank the keys it omits."""
        from apps.content.models import HomeSection

        section = HomeSection.objects.create(
            key="overlay-test",
            data={"hero": {"heading": "عنوان", "eyebrow": "فرعي"}, "kept": "قيمة"},
            data_en={"hero": {"heading": "Heading"}},
        )

        with translation.override("en"):
            resolved = section.resolved_data()

        assert resolved["hero"]["heading"] == "Heading"
        assert resolved["hero"]["eyebrow"] == "فرعي", "an omitted key was blanked"
        assert resolved["kept"] == "قيمة"

    def test_arabic_ignores_the_overlay_entirely(self, db):
        from apps.content.models import HomeSection

        section = HomeSection.objects.create(
            key="overlay-ar", data={"a": "عربي"}, data_en={"a": "English"}
        )

        with translation.override("ar"):
            assert section.resolved_data()["a"] == "عربي"

    def test_list_items_merge_by_position(self, db):
        from apps.content.models import HomeSection

        section = HomeSection.objects.create(
            key="overlay-list",
            data={"items": [{"title": "أ"}, {"title": "ب"}]},
            data_en={"items": [{"title": "A"}]},
        )

        with translation.override("en"):
            items = section.resolved_data()["items"]

        assert items[0]["title"] == "A"
        assert items[1]["title"] == "ب", "the untranslated item was dropped"


class TestCatalogueRegression:
    def test_the_catalogue_renders_the_same_in_arabic_as_before(self, storefront):
        """FR-131: the approved Arabic storefront is the contract. Adding a
        second language must not have moved a single word of it."""
        switch(storefront, "ar")
        html = storefront.get(reverse("storefront:shop")).content.decode()

        for expected in ("أقفال بالبصمة", "المتجر", "تسوق الآن"):
            assert expected in html
