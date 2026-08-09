"""Form hardening across the storefront (T-1604 – T-1606, FR-134).

FR-134 has three clauses and they are checked separately here, because each one
fails differently:

``method="post"``
    asserted from both ends — no template offers a mutating endpoint through a
    link or a GET form, and the endpoint itself refuses GET. A form that merely
    *says* ``post`` while the view would happily act on a GET is not hardened;
    it is one crawler away from a stranger emptying a cart.
``{% csrf_token %}``
    every POST form in ``templates/`` must contain the tag. Missing it turns a
    working form into a 403 for real customers, which is the kind of defect that
    passes review and fails in production.
``hidden identifiers``
    a form that acts on one record has to say which record. The mapping below is
    per endpoint, because "some hidden input exists" would be satisfied by the
    ``next`` field every form already carries.

The requirement ends with **"without visual change"**, and that clause is
checked too: every field these forms added for the server's benefit has to
render as ``type="hidden"``. An identifier the customer can see — or edit — is
both a visual regression and a tampering surface.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

TEMPLATE_ROOT = Path(settings.BASE_DIR) / "templates"

FORM_BLOCK = re.compile(r"<form\b.*?</form>", re.S)
ANCHOR = re.compile(r"<a\b[^>]*>", re.S)
URL_TAG = re.compile(r"\{%\s*url\s+'storefront:([a-z0-9-]+)'")

#: Every storefront endpoint that changes state. All of them are ``@require_POST``
#: in ``storefront/views.py``; listing them here rather than introspecting the
#: decorator keeps the contract readable, and the first test proves the list and
#: the code still agree.
MUTATING_ENDPOINTS = (
    "cart-add",
    "cart-update",
    "cart-remove",
    "cart-coupon",
    "wishlist-toggle",
    "newsletter",
    "contact-send",
    "checkout-submit",
    "account-login",
    "account-register",
    "account-logout",
    "address-create",
    "address-delete",
    "profile-update",
    "password-reset-request",
)

#: endpoint → the field naming the record it acts on.
REQUIRED_IDENTIFIER = {
    "cart-add": "variant",
    "cart-update": "variant",
    "cart-remove": "variant",
    "wishlist-toggle": "product",
    "address-delete": "address",
    "checkout-submit": "idempotency_key",
}

#: Fields added for the server that the customer must never see.
INVISIBLE_FIELDS = frozenset(
    {"csrfmiddlewaretoken", "next", "idempotency_key", "product", "address"}
)


class _Inputs(HTMLParser):
    """Collect ``(name, type)`` for every input, attribute order be damned."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inputs: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        if tag != "input":
            return
        attributes = dict(attrs)
        self.inputs.append((attributes.get("name", ""), attributes.get("type", "text")))


def _post_forms():
    """(template path, line number, endpoint name, form source) per POST form."""
    for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
        text = template.read_text(encoding="utf-8")
        for match in FORM_BLOCK.finditer(text):
            body = match.group(0)
            open_tag = body[: body.index(">") + 1]
            method = re.search(r'method="([^"]*)"', open_tag)
            if not method or method.group(1).lower() != "post":
                continue
            endpoint = URL_TAG.search(open_tag)
            yield (
                template.relative_to(settings.BASE_DIR),
                text[: match.start()].count("\n") + 1,
                endpoint.group(1) if endpoint else "",
                body,
            )


def test_every_mutating_endpoint_refuses_a_get(storefront):
    """FR-134's ``method="post"`` has to be true of the endpoint, not only of the markup."""
    offenders = []
    for endpoint in MUTATING_ENDPOINTS:
        response = storefront.get(reverse(f"storefront:{endpoint}"))
        if response.status_code != 405:
            offenders.append(f"{endpoint} answered GET with {response.status_code}")
    assert offenders == [], f"a mutation is reachable without a POST: {offenders}"


def test_no_link_or_get_form_offers_a_mutating_endpoint():
    """The other end of FR-134's ``method="post"``: a mutation behind an ``<a
    href>`` is a mutation any prefetch can fire."""
    offenders = []
    for template in sorted(TEMPLATE_ROOT.rglob("*.html")):
        text = template.read_text(encoding="utf-8")
        relative = template.relative_to(settings.BASE_DIR)

        for anchor in ANCHOR.finditer(text):
            named = URL_TAG.search(anchor.group(0))
            if named and named.group(1) in MUTATING_ENDPOINTS:
                line = text[: anchor.start()].count("\n") + 1
                offenders.append(f"{relative}:{line} links to {named.group(1)}")

        for match in FORM_BLOCK.finditer(text):
            body = match.group(0)
            open_tag = body[: body.index(">") + 1]
            named = URL_TAG.search(open_tag)
            if not named or named.group(1) not in MUTATING_ENDPOINTS:
                continue
            method = re.search(r'method="([^"]*)"', open_tag)
            if not method or method.group(1).lower() != "post":
                line = text[: match.start()].count("\n") + 1
                offenders.append(f"{relative}:{line} posts {named.group(1)} by GET")

    assert offenders == [], f"mutating endpoints reachable without a POST form: {offenders}"


def test_every_post_form_carries_a_csrf_token():
    """FR-134's ``{% csrf_token %}`` clause, checked at the source."""
    missing = [
        f"{path}:{line} ({endpoint or 'no named endpoint'})"
        for path, line, endpoint, body in _post_forms()
        if "{% csrf_token %}" not in body
    ]
    assert missing == [], f"POST forms without a CSRF token: {missing}"


def test_every_record_form_names_the_record_it_acts_on():
    """FR-134's hidden-identifier clause, per endpoint.

    ``next`` is on nearly every form, so "has a hidden input" proves nothing.
    What matters is that a cart line form says *which* line.
    """
    missing = []
    for path, line, endpoint, body in _post_forms():
        field = REQUIRED_IDENTIFIER.get(endpoint)
        if field and f'name="{field}"' not in body:
            missing.append(f"{path}:{line} ({endpoint}) has no {field!r} field")
    assert missing == [], f"forms that cannot identify their record: {missing}"

    covered = {endpoint for _p, _l, endpoint, _b in _post_forms()}
    orphans = sorted(set(REQUIRED_IDENTIFIER) - covered)
    assert orphans == [], (
        f"REQUIRED_IDENTIFIER names endpoints no template posts to: {orphans}"
    )


def test_the_added_fields_are_hidden_so_the_page_looks_unchanged(storefront):
    """The "without visual change" half of FR-134, on the rendered page."""
    from apps.catalog.models import Product

    variant = Product.objects.get(slug="zakey-apex-pro").variants.first()
    storefront.post(
        reverse("storefront:cart-add"), {"variant": variant.pk, "quantity": 1}, follow=True
    )

    offenders = []
    for path in (
        "/",
        "/shop/",
        "/products/zakey-apex-pro/",
        "/cart/",
        "/checkout/",
        "/wishlist/",
        "/account/",
        "/contact/",
        "/about/",
    ):
        parser = _Inputs()
        parser.feed(storefront.get(path).content.decode())
        for name, kind in parser.inputs:
            if name in INVISIBLE_FIELDS and kind != "hidden":
                offenders.append(f"{path}: {name} renders as type={kind!r}")

    assert offenders == [], (
        f"server-side identifiers became visible form controls: {offenders}"
    )
