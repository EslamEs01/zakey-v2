"""Template hygiene guards (T-1902, NFR-009).

These exist because of a real defect: a multi-line ``{# ... #}`` comment in
``shop.html`` rendered as literal page text, and because the text happened to
contain the word ``<template>`` the browser parsed it as a real element and
swallowed 19KB of the catalogue — the filter sidebar, every product card and the
pagination. The server response was a perfectly valid 200 containing all the
right strings, so nothing server-side noticed. Only a browser did.

That is the whole argument for these tests: source inspection cannot see this
class of bug, and neither can a response-body assertion.
"""

from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

TEMPLATE_ROOT = Path(settings.BASE_DIR) / "templates"


class TemplateCommentTests(SimpleTestCase):
    def test_no_multiline_hash_comments(self):
        """``{#`` is single-line. Without ``#}`` on the same line Django does not
        treat it as a comment at all and emits the text into the page."""
        offenders = []
        for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
            for number, line in enumerate(
                template.read_text(encoding="utf-8").splitlines(), 1
            ):
                if "{#" in line and "#}" not in line.split("{#", 1)[1]:
                    offenders.append(f"{template.relative_to(settings.BASE_DIR)}:{number}")
        self.assertEqual(
            offenders,
            [],
            "multi-line {# #} comments render as page text; use {% comment %}: "
            f"{offenders}",
        )

    def test_no_unclosed_comment_markers(self):
        """A stray ``#}`` without an opener is equally invisible server-side."""
        offenders = []
        for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
            text = template.read_text(encoding="utf-8")
            if text.count("{% comment %}") != text.count("{% endcomment %}"):
                offenders.append(str(template.relative_to(settings.BASE_DIR)))
        self.assertEqual(offenders, [], f"unbalanced comment blocks: {offenders}")


class RenderedMarkupTests(SimpleTestCase):
    """Assert on the *parsed* shape, not on substrings.

    ``"filter-sidebar" in response.content`` was true throughout the bug. What
    was false was that the browser could find the element.
    """

    databases = {"default"}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.core.management import call_command

        call_command("seed_demo", verbosity=0)

    def _fragment(self, path):
        from html.parser import HTMLParser

        class Collector(HTMLParser):
            def __init__(self):
                super().__init__(convert_charrefs=True)
                self.template_depth = 0
                self.outside = []   # (tag, attrs) seen outside any <template>
                self.stray_text = []

            def handle_starttag(self, tag, attrs):
                if tag == "template":
                    self.template_depth += 1
                    return
                if self.template_depth == 0:
                    self.outside.append((tag, dict(attrs)))

            def handle_endtag(self, tag):
                if tag == "template" and self.template_depth:
                    self.template_depth -= 1

            def handle_data(self, data):
                if "{#" in data or "#}" in data or "{%" in data or "{{" in data:
                    self.stray_text.append(data.strip()[:120])

        parser = Collector()
        parser.feed(self.client.get(path).content.decode())
        return parser

    def test_catalogue_markup_is_not_trapped_inside_a_template(self):
        parsed = self._fragment("/shop/")
        classes = [
            attrs.get("class", "") for _tag, attrs in parsed.outside
        ]
        self.assertTrue(
            any("filter-sidebar" in value for value in classes),
            "the filter sidebar is not reachable outside a <template> element",
        )
        cards = [a for _t, a in parsed.outside if "data-product-card" in a]
        self.assertGreater(len(cards), 0, "no product card is reachable in the parsed DOM")

    def test_no_template_syntax_leaks_into_any_public_page(self):
        """A visible ``{#``/``{%``/``{{`` is an unrendered token on the page."""
        for path in ("/", "/shop/", "/cart/", "/checkout/", "/account/", "/contact/", "/about/"):
            with self.subTest(path=path):
                parsed = self._fragment(path)
                self.assertEqual(
                    parsed.stray_text, [], f"{path} shows raw template syntax"
                )


JS_ROOTS = (
    Path(settings.BASE_DIR) / "static" / "src" / "js",
    Path(settings.BASE_DIR) / "static" / "dist" / "js",
)

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)


def _executable_javascript(text: str) -> str:
    """``text`` with its comments removed.

    Every module in ``static/src/js`` opens with a block comment describing the
    business rule it *used* to own — ``pages/checkout.js`` quotes the retired
    VAT extraction verbatim, ``Math.round((total * vatRate) / (1 + vatRate))``.
    Scanning raw source would therefore fail on the very documentation that
    records the rule's removal. Only whole-line ``//`` comments are stripped, so
    a ``https://`` inside a string is never mistaken for one.
    """
    without_blocks = _BLOCK_COMMENT.sub("", text)
    return "\n".join(
        line
        for line in without_blocks.splitlines()
        if not line.lstrip().startswith("//")
    )


class ShippedScriptTests(SimpleTestCase):
    """No business rule survives in the browser (T-1607, FR-133).

    This is a negative requirement, so the only honest proof is a scan: read
    every script the storefront actually ships and show the arithmetic is not
    there. The prototype priced the basket, applied the coupon, extracted VAT
    and picked a shipping method client-side; the server owns all four now, and
    a second implementation in JavaScript would not merely be redundant — it
    would be the one the customer sees, and the one the customer can edit.

    Deliberately *not* forbidden: ``shipping`` and ``payment``. Both appear as
    the names of checkout steps and form fields. Naming a method is
    presentation; choosing one, or pricing it, is a business rule.
    """

    #: Vocabulary a presentation-only script has no innocent use for. Matched
    #: at the start of an identifier (case-insensitive) so ``vatRate`` is caught
    #: while ``activate`` is not.
    MONEY_WORDS = ("price", "subtotal", "total", "vat", "discount", "coupon", "amount")

    #: The prototype rendered money through ``Intl.NumberFormat`` in cart.js,
    #: checkout.js and wishlist.js (frontend-contract.md §1). A script that
    #: formats currency is a script that produced a number.
    FORMATTERS = ("Intl.NumberFormat", "toFixed", "formatCurrency", "formatMoney")

    #: The commerce constants the prototype hard-coded in the browser: the VAT
    #: rate, the free-shipping threshold, and the coupon rule's field names.
    CONSTANTS = (
        "0.14",
        "1500",
        "vatRate",
        "freeShippingThreshold",
        "discountRate",
        "minimumSubtotal",
    )

    def _sources(self):
        for root in JS_ROOTS:
            for path in sorted(root.rglob("*.js")):
                yield path, _executable_javascript(path.read_text(encoding="utf-8"))

    def test_no_shipped_script_names_a_money_value(self):
        """A script that cannot name a price cannot compute one."""
        pattern = re.compile(
            r"(?<![A-Za-z])(" + "|".join(self.MONEY_WORDS) + r")", re.IGNORECASE
        )
        offenders = []
        for path, code in self._sources():
            for match in pattern.finditer(code):
                line = code[: match.start()].count("\n") + 1
                offenders.append(
                    f"{path.relative_to(settings.BASE_DIR)}:{line}: {match.group(0)}"
                )
        self.assertEqual(
            offenders,
            [],
            "money vocabulary is back in shipped JavaScript; the server owns "
            f"these numbers: {offenders}",
        )

    def test_no_shipped_script_formats_currency_or_holds_a_commerce_constant(self):
        offenders = []
        for path, code in self._sources():
            for token in (*self.FORMATTERS, *self.CONSTANTS):
                if token in code:
                    offenders.append(f"{path.relative_to(settings.BASE_DIR)}: {token}")
        self.assertEqual(
            offenders,
            [],
            f"a shipped script prices or formats money again: {offenders}",
        )

    def test_the_browser_is_not_handed_the_inputs_a_business_rule_needs(self):
        """The other half of the same guarantee.

        Removing the arithmetic is not enough if the page still ships the
        catalogue, the coupon rules and the VAT rate to the browser: the rule
        could simply be rewritten. ``client_payload`` is the sole producer of
        the ``#zakey-fixture`` payload (``base.html:23``), and its key set is
        frozen to formatting metadata.
        """
        from apps.core.models import SiteSetting
        from storefront.context import client_payload

        payload = client_payload(SiteSetting())

        self.assertEqual(
            sorted(payload),
            ["currency", "direction", "locale", "maxLineQuantity"],
            "the client payload grew a key; anything beyond formatting metadata "
            "hands a business rule back to the browser",
        )
