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
