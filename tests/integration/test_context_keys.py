"""Context-key preservation across the fixture → database swap (T-1601 – T-1608, FR-130).

FR-130 is a *compatibility* requirement. The views were allowed to change where
their data comes from; they were not allowed to change what the templates are
handed. So these assertions are deliberately about the **keys**, not the values:
the frozen sets below are read straight off the prototype's own views at commit
``98237d7`` — ``storefront/views.py`` plus ``fixture_provider.page_context`` /
``get_site_context`` — which is the tree ``frontend-contract.md`` was extracted
from. If a later refactor renames a context key, the templates have to change
with it, and that is exactly the cost FR-130 exists to prevent.

Two keys the prototype supplied are deliberately gone, and their absence is the
point rather than a regression:

``fixture``
    the entire catalogue JSON, handed to every single template. Nothing under
    ``templates/`` reads it any more; leaving it in place would have kept the
    JSON fixture on the request path, which is precisely what T-1608 removed.
``prototypeNotice`` (product page only)
    a top-level duplicate of ``site.prototypeNotice``. No template ever
    referenced the top-level copy — the notice is read from ``site``, where it
    still is.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

#: Supplied to every page by ``fixture_provider.page_context`` in the prototype
#: and by ``storefront.context.page_context`` now.
SHARED_KEYS = frozenset(
    {
        "site",
        "navigation",
        "categories",
        "collections",
        "client_fixture",
        "page_id",
        "page_state",
    }
)

#: route name → (reverse kwargs, query string, keys that page's view added on
#: top of ``SHARED_KEYS`` in the prototype).
PAGES = (
    ("storefront:home", None, {}, frozenset({"best_sellers", "featured", "home_reviews"})),
    ("storefront:shop", None, {}, frozenset({"catalogue"})),
    ("storefront:collection", {"slug": "fingerprint-locks"}, {}, frozenset({"catalogue"})),
    ("storefront:search", None, {"q": "ذكي"}, frozenset({"catalogue"})),
    (
        "storefront:product",
        {"slug": "zakey-apex-pro"},
        {},
        frozenset(
            {
                "product",
                "relatedProducts",
                "reviews",
                "faqs",
                "selectedImageId",
                "selectedFinishId",
            }
        ),
    ),
    ("storefront:cart", None, {}, frozenset()),
    ("storefront:checkout", None, {}, frozenset({"checkout_step"})),
    ("storefront:wishlist", None, {}, frozenset()),
    ("storefront:account", None, {}, frozenset({"account_mode", "account_tab"})),
    ("storefront:about", None, {}, frozenset()),
    ("storefront:contact", None, {}, frozenset()),
    ("storefront:error-404", None, {}, frozenset()),
    ("storefront:error-500", None, {}, frozenset()),
)


@pytest.mark.parametrize(
    "name,kwargs,query,page_keys", PAGES, ids=[page[0] for page in PAGES]
)
def test_every_page_still_hands_the_templates_the_prototype_context_keys(
    storefront, name, kwargs, query, page_keys
):
    response = storefront.get(reverse(name, kwargs=kwargs), query)
    missing = sorted(key for key in SHARED_KEYS | page_keys if key not in response.context)
    assert missing == [], (
        f"{name} no longer supplies {missing}; the approved templates read these "
        "keys, so renaming one forces a template change FR-130 forbids"
    )


def test_no_page_context_still_carries_the_fixture_payload(storefront):
    """The swap really happened: no template is handed the catalogue JSON."""
    for name, kwargs, query, _page_keys in PAGES:
        response = storefront.get(reverse(name, kwargs=kwargs), query)
        assert "fixture" not in response.context, (
            f"{name} still puts the whole JSON fixture in its context; the views "
            "are supposed to read services and QuerySets now"
        )


def test_no_storefront_module_imports_a_fixture_provider():
    """An AST import scan, not a substring scan.

    ``views.py`` and ``context.py`` both *mention* ``fixture_provider`` in prose
    to explain what replaced it, so grepping for the name would fail on the
    documentation. Only a real import counts as a fixture call surviving.
    """
    assert importlib.util.find_spec("storefront.fixture_provider") is None, (
        "storefront.fixture_provider is importable again (T-1608 deleted it)"
    )

    offenders = []
    for path in sorted((Path(settings.BASE_DIR) / "storefront").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""] + [alias.name for alias in node.names]
            else:
                continue
            if any("fixture_provider" in name for name in names):
                offenders.append(f"{path.name}:{node.lineno}")
    assert offenders == [], f"a fixture provider is imported again: {offenders}"


def test_the_values_behind_the_frozen_keys_come_from_the_database(storefront):
    """Same key, new source.

    Editing the row has to change what the template is handed — otherwise the
    key survived but the QuerySet behind it did not.
    """
    from apps.catalog.models import Product

    edited = "اسم مُحدَّث من قاعدة البيانات"
    Product.objects.filter(slug="zakey-apex-pro").update(name=edited)

    detail = storefront.get(reverse("storefront:product", kwargs={"slug": "zakey-apex-pro"}))
    assert detail.context["product"]["name"] == edited

    listing = storefront.get(reverse("storefront:shop"))
    names = {item["name"] for item in listing.context["catalogue"]["products"]}
    assert edited in names, "the shop catalogue is not reading the product table"
