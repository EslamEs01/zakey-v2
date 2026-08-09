"""The no-JavaScript notice (FR-136, NFR-010).

The old notice told visitors: *"you can browse pages and products; to run the
cart, filters and wishlist please enable JavaScript."* That was true of the
prototype and false of this build — `tests/e2e/no-js.spec.js` now drives a
customer through add-to-cart, quantity change, removal, catalogue sorting and
checkout with `javaScriptEnabled: false`. The page was telling customers a
working feature was unavailable.

What replaced it says the true thing: scripting is needed for the *interactive*
layer — dropdown menus, dialogs — and not for shopping. It is bilingual, because
a visitor who has scripting switched off is disproportionately likely to be on a
hardened or assistive setup, and the rest of the storefront's Arabic gives them
nothing to act on if Arabic is not their language.

None of it is visible in a normal capture: `<noscript>` content is not rendered
by a browser with scripting enabled, which is why the seven visual comparisons
awaiting approval are untouched by this change.
"""

from __future__ import annotations

import re

import pytest
from django.template.loader import render_to_string
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db

NOSCRIPT_RE = re.compile(r"<noscript>(.*?)</noscript>", re.S)

#: Wording that would mean someone shipped a draft.
FORBIDDEN = ("TODO", "FIXME", "XXX", "Lorem", "placeholder", "PLACEHOLDER", "طوطو", "نص تجريبي")

ROUTES = ["storefront:home", "storefront:shop", "storefront:cart", "storefront:contact"]


def _notice(html: str) -> str:
    match = NOSCRIPT_RE.search(html)
    assert match, "the page rendered no <noscript> block at all"
    return match.group(1)


@pytest.fixture
def home_html(seeded_catalogue):
    return Client().get(reverse("storefront:home")).content.decode()


class TestTheNoticeIsPresentAndScoped:
    @pytest.mark.parametrize("route", ROUTES)
    def test_every_page_carries_it(self, seeded_catalogue, route):
        """FR-136: it lives in the base template, so no page can be missing it."""
        html = Client().get(reverse(route)).content.decode()

        assert _notice(html).strip(), f"{route} rendered an empty notice"

    def test_the_text_exists_only_inside_the_noscript_element(self, home_html):
        """FR-136: nothing here may reach a scripted browser.

        `<noscript>` is not rendered when scripting is on, so a stray copy of the
        sentence outside the element would appear on every page — and in every
        visual snapshot.
        """
        notice = _notice(home_html)
        outside = home_html.replace(notice, "")

        assert "JavaScript" not in outside
        assert "جافاسكريبت" not in outside

    def test_it_keeps_the_established_notice_styling(self, home_html):
        """The design was not redecorated to deliver a copy fix."""
        assert 'class="noscript-note"' in _notice(home_html)


class TestWhatItSays:
    def test_it_names_javascript_as_needed_for_interactive_features(self, home_html):
        notice = _notice(home_html)

        assert "جافاسكريبت مطلوب للعناصر التفاعلية" in notice
        assert "JavaScript is required for interactive storefront features" in notice

    def test_it_no_longer_claims_shopping_needs_javascript(self, home_html):
        """The specific falsehood this replaced, pinned so it cannot come back.

        The no-JS suite proves the cart works without scripting; a notice saying
        otherwise contradicts the tests that guard FR-136.
        """
        notice = _notice(home_html)

        assert "لتشغيل السلة والفلاتر والمفضلة يرجى تفعيل" not in notice
        assert "التصفح والشراء وإتمام الطلب تعمل بدونه" in notice
        assert "Browsing, shopping and checkout work without it" in notice

    def test_it_carries_no_draft_or_debug_wording(self, home_html):
        notice = _notice(home_html)

        found = [token for token in FORBIDDEN if token in notice]
        assert found == [], f"draft wording reached the storefront: {found}"


class TestDirectionAndLanguage:
    def test_each_language_declares_itself(self, home_html):
        """NFR-010: a Latin run inside an RTL page needs its own direction.

        Without `dir="ltr"` the English sentence is reordered by the RTL context
        and its trailing punctuation jumps to the wrong end; without `lang` a
        screen reader reads English with Arabic phonemes.
        """
        notice = _notice(home_html)

        assert '<span lang="ar" dir="rtl">' in notice
        assert '<span lang="en" dir="ltr">' in notice

    def test_the_page_direction_itself_is_unchanged(self, home_html):
        assert '<html lang="ar-EG" dir="rtl">' in home_html

    def test_the_notice_renders_from_the_base_template_directly(self):
        """A template-level test, independent of any view or database row."""
        html = render_to_string("base.html", {"page_id": "home", "page_state": "default"})

        notice = _notice(html)
        assert 'lang="ar"' in notice and 'lang="en"' in notice
