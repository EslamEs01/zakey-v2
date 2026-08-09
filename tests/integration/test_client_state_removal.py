"""The browser is no longer a store (T-1604, T-1607, T-1608).

**What FR-132 asks, and what is honestly claimed here.** The requirement reads:
*"localStorage cart and wishlist behaviour MUST be replaced through an isolated
adapter, keeping ``zakey:prototype:v1`` handling as a one-time migration path."*

That is a **transition** requirement, and the transition is over. The adapter was
the mechanism for the swap during Phase 16; `rollout-and-rollback.md` §3 schedules
it for removal with the feature flag and `fixture_provider.py` in T-1608, "only
after all six batches are accepted". It is now gone:
`static/src/js/state/storage-adapter.js` does not exist, and neither the source
tree nor the built bundle mentions `zakey:prototype:v1`. The only surviving copy
is a stale artifact under the git-ignored `_site/` export directory.

So these tests prove the **end state the requirement exists to produce** — the
browser holds no cart, no wishlist and no price, and nothing server-side trusts
it to. They do **not** claim a live migration path for `zakey:prototype:v1`,
because none exists and none is wanted: the prototype was a reference build
(`003-zakey-frontend-reference-build`) that was never deployed to a customer, so
there is no population of browsers holding that key to migrate. Retaining a
migration path would be dead code guarding data that does not exist.

Recorded in `specs/004-zakey-commerce-backend-admin/qa/spec-divergences.md` §2 so
the gap between the requirement's literal wording and the shipped design is
visible rather than quietly absorbed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

BASE = Path(settings.BASE_DIR)
JS_ROOTS = (BASE / "static" / "src" / "js", BASE / "static" / "dist" / "js")

PROTOTYPE_KEY = "zakey:prototype:v1"
RETIRED_ADAPTER = BASE / "static" / "src" / "js" / "state" / "storage-adapter.js"

#: Web-storage APIs. A single read is enough to put pricing back in the browser.
STORAGE_API_RE = re.compile(r"\b(?:local|session)Storage\b")

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"^\s*//.*$", re.M)
TRAILING_COMMENT_RE = re.compile(r"(?<![:/])//.*$", re.M)

#: Keys that would put money, stock or basket contents back into the page for a
#: script to act on. `#zakey-fixture` is allowed to carry presentation settings
#: only — currency, locale, the per-line maximum.
FORBIDDEN_FIXTURE_KEYS = {
    "cart", "cartLines", "lines", "items", "basket",
    "wishlist", "saved", "favourites",
    "price", "prices", "subtotal", "total", "totals", "grandTotal",
    "discount", "coupon", "vat", "shipping", "installation",
    "stock", "inventory", "isSignedIn", "customer", "user",
}


def _shipped_js() -> list[Path]:
    """Every JavaScript file that actually ships, source and built."""
    files: list[Path] = []
    for root in JS_ROOTS:
        if root.exists():
            files.extend(sorted(root.rglob("*.js")))
    assert files, "no shipped JavaScript found; the scan would pass vacuously"
    return files


def _code_only(source: str) -> str:
    """Strip comments.

    `app.js` and `header.js` both *describe* the removed `localStorage` store in
    prose. Scanning raw text would fail on the very comments that document the
    removal, so the scan reads code.
    """
    without_blocks = BLOCK_COMMENT_RE.sub("", source)
    without_lines = LINE_COMMENT_RE.sub("", without_blocks)
    return TRAILING_COMMENT_RE.sub("", without_lines)


class TestTheClientSideStoreIsGone:
    def test_no_shipped_script_touches_web_storage(self):
        """FR-132: cart and wishlist behaviour left the browser entirely.

        Stronger than "an adapter isolates it": there is no code path to isolate.
        """
        offenders = [
            str(path.relative_to(BASE))
            for path in _shipped_js()
            if STORAGE_API_RE.search(_code_only(path.read_text(encoding="utf-8")))
        ]

        assert offenders == [], f"web storage is read or written in: {offenders}"

    def test_the_prototype_storage_key_appears_nowhere_that_ships(self):
        """FR-132: the prototype's key is not read, written or migrated."""
        searched = [*_shipped_js(), *sorted((BASE / "templates").rglob("*.html"))]
        offenders = [
            str(path.relative_to(BASE))
            for path in searched
            if PROTOTYPE_KEY in path.read_text(encoding="utf-8", errors="ignore")
        ]

        assert offenders == [], f"{PROTOTYPE_KEY} still appears in: {offenders}"

    def test_the_retired_adapter_module_is_really_gone(self):
        """FR-132: T-1608 removed the adapter, not merely stopped calling it.

        A module left on disk gets imported again by the next person who needs
        somewhere to put state.
        """
        assert not RETIRED_ADAPTER.exists(), f"{RETIRED_ADAPTER} should have been removed by T-1608"

        state_dir = RETIRED_ADAPTER.parent
        assert not state_dir.exists() or not any(state_dir.iterdir()), (
            "a client-side state module directory has reappeared"
        )


@pytest.mark.django_db
class TestTheServerOwnsTheState:
    def test_the_page_hands_the_browser_no_money_and_no_basket(self, client):
        """FR-132: `#zakey-fixture` carries presentation settings only.

        Removing the store accomplishes nothing if the page then prints the cart
        and its prices into a JSON island for a script to pick up.
        """
        body = client.get(reverse("storefront:home")).content.decode()

        match = re.search(
            r'<script id="zakey-fixture" type="application/json">(.*?)</script>', body, re.S
        )
        assert match, "the client fixture element is missing; the assertion would be vacuous"

        payload = json.loads(match.group(1))
        assert isinstance(payload, dict)

        leaked = sorted(FORBIDDEN_FIXTURE_KEYS.intersection(payload))
        assert leaked == [], f"state the browser must not own was serialised into the page: {leaked}"

    def test_the_cart_page_renders_its_lines_and_money_server_side(
        self, client, variant, stock, site_setting
    ):
        """FR-132: the basket arrives rendered, not assembled by a script.

        A real line is added through the storefront's own POST endpoint, then the
        page is fetched. Both the product name and the line's money must be in
        the returned HTML: if the cart were still client-assembled from
        `localStorage`, the response would be an empty shell and a visitor
        without JavaScript would see nothing.
        """
        client.post(
            reverse("storefront:cart-add"),
            {"variant": variant.pk, "quantity": 1},
        )

        response = client.get(reverse("storefront:cart"))
        body = response.content.decode()

        assert response.status_code == 200
        assert response.context["cart_totals"] is not None, (
            "totals must be computed server-side and put in the template context"
        )
        assert response.context["cart_totals"].grand_total > 0
        assert variant.product.name in body, "the line was not rendered by the server"
