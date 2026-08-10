"""Database-backed storefront context (T-1601 – T-1608, FR-130, FR-131).

This module replaces ``storefront.fixture_provider`` as the request-time source
of truth. Every value the storefront renders now comes from the database:

* commerce numbers (VAT rate, free-shipping threshold, currency) from
  :class:`apps.core.models.SiteSetting`;
* catalogue taxonomy from :mod:`apps.catalog`;
* page copy from :class:`apps.content.models.HomeSection` (staff-editable);
* geography, shipping and payment options from :mod:`apps.shipping` and
  :mod:`apps.payments`.

The **output shape is deliberately identical** to the fixture's, so the approved
templates render byte-for-byte the same markup (frontend-contract.md §3). The
shape is the contract; the fixture is no longer its source.

What is *not* here matters just as much. The client payload
(:func:`client_payload`) carries presentation settings only. Products, prices,
reviews, coupon rules, prototype accounts, prototype carts and prototype
wishlists are **not** shipped to the browser any more: those are business
authority and they stay on the server (FR-133, FR-136, threat T-03).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.core.models import PublicationStatus, SiteSetting


# ---------------------------------------------------------------------------
# Catalogue taxonomy
# ---------------------------------------------------------------------------


def _category_record(category) -> dict[str, Any]:
    """A category in the shape the approved templates already consume."""
    record = {
        "id": category.legacy_id or category.slug,
        "slug": category.slug,
        "name": category.name,
        "description": category.description,
        "kind": category.kind,
    }
    if category.image_src:
        record["image"] = {
            "path": category.image_src,
            "width": category.image_width,
            "height": category.image_height,
            "alt": category.image_alt,
        }
    return record


def published_categories() -> list[dict[str, Any]]:
    from apps.catalog.models import Category

    return [
        _category_record(category)
        for category in Category.objects.filter(status=PublicationStatus.PUBLISHED)
    ]


def published_collections() -> list[dict[str, Any]]:
    from apps.catalog.models import Collection

    return [
        {
            "id": collection.legacy_id or collection.slug,
            "slug": collection.slug,
            "name": collection.name,
            "description": collection.description,
            "eyebrow": collection.promotion_eyebrow,
            "tone": collection.promotion_tone,
        }
        for collection in Collection.objects.filter(status=PublicationStatus.PUBLISHED)
    ]


# ---------------------------------------------------------------------------
# Page copy (staff-editable, was `site.*` in the fixture)
# ---------------------------------------------------------------------------


def page_copy() -> dict[str, Any]:
    """All active ``HomeSection`` payloads keyed by section key.

    One query for every block of authored copy on the site.
    """
    from apps.content.models import HomeSection

    return {
        section.key: section.data or {}
        for section in HomeSection.objects.filter(is_active=True)
    }


def site_settings_record(setting: SiteSetting) -> dict[str, Any]:
    return {
        "currency": {
            "code": setting.currency_code,
            "label": setting.currency_label,
            "decimalPlaces": setting.currency_decimal_places,
        },
        "vatRate": float(setting.vat_rate),
        "freeShippingThreshold": int(setting.free_shipping_threshold),
        "maxLineQuantity": setting.max_line_quantity,
        "prototypeNotice": setting.prototype_notice,
    }


def build_site(setting: SiteSetting, copy: dict[str, Any]) -> dict[str, Any]:
    """Assemble the ``site`` context the templates expect.

    Commerce numbers come from ``SiteSetting`` (never from authored copy) so a
    content edit can never move VAT or the free-shipping threshold.
    """
    site = dict(copy)  # brand / announcement / home / about / contact / footer
    site.update(site_settings_record(setting))
    site["locale"] = "ar-EG"
    site["direction"] = "rtl"
    return site


# ---------------------------------------------------------------------------
# Navigation, content and geography
# ---------------------------------------------------------------------------


def navigation() -> dict[str, list[dict[str, Any]]]:
    from apps.content.models import NavigationGroup, NavigationItem

    groups: dict[str, list[dict[str, Any]]] = {"primary": [], "utility": [], "footer": []}
    key_for = {
        NavigationGroup.PRIMARY: "primary",
        NavigationGroup.UTILITY: "utility",
        NavigationGroup.FOOTER: "footer",
    }
    for item in NavigationItem.objects.filter(is_active=True):
        groups[key_for[item.group]].append(
            {
                "id": item.pk,
                "label": item.label,
                "href": item.href,
                "routeName": item.route_name,
                "icon": item.icon,
            }
        )
    return groups


def partners() -> list[dict[str, Any]]:
    from apps.content.models import Partner

    return [
        {
            "name": partner.name,
            "mark": {
                "path": partner.logo.url if partner.logo else partner.legacy_image_path,
                "width": 160,
                "height": 64,
                "alt": partner.name,
            },
        }
        for partner in Partner.objects.filter(is_active=True)
    ]


def team_members() -> list[dict[str, Any]]:
    """The about-page roster, stored as copy on the ``team`` content section."""
    from apps.content.models import HomeSection

    section = HomeSection.objects.filter(key="team", is_active=True).first()
    if section is None:
        return []
    return section.data.get("members", [])


def faqs(page: str = "") -> list[dict[str, Any]]:
    from apps.content.models import FAQ

    queryset = FAQ.objects.filter(is_active=True)
    if page:
        queryset = queryset.filter(page=page)
    return [
        {
            "id": faq.legacy_id or str(faq.pk),
            "question": faq.question,
            "answer": faq.answer,
            "page": faq.page,
        }
        for faq in queryset
    ]


def governorates() -> list[dict[str, Any]]:
    from apps.shipping.models import Governorate

    return [
        {"key": gov.key, "name": gov.name}
        for gov in Governorate.objects.filter(is_active=True)
    ]


def service_eligibility() -> dict[str, list[dict[str, Any]]]:
    from apps.shipping.models import ServiceArea

    areas = ServiceArea.objects.filter(is_active=True).select_related("governorate")
    return {
        "areas": [
            {
                "key": area.key,
                "name": area.name,
                "governorate": area.governorate.key,
                "governorateName": area.governorate.name,
                "sameDay": area.same_day_eligible,
                "installation": area.installation_eligible,
            }
            for area in areas
        ]
    }


def shipping_options() -> list[dict[str, Any]]:
    """Shipping methods as the checkout template renders them.

    Prices are **not** included here: the quote is computed server-side against
    the real basket and destination (FR-041), never picked in the browser.

    Only methods that still have an active rate are offered. The approved launch
    policy withdraws paid shipping by deactivating its *rates*, not its methods
    (T-2006), so filtering on the method alone kept listing «شحن قياسي» and
    «توصيل في اليوم نفسه» as selectable. `quote_shipping` refused them on submit,
    so no customer could ever have been charged an unapproved rate — but the
    form offered two choices that could only ever fail.

    The filter is deliberately coarser than `available_methods`: a method with no
    active rate anywhere cannot be quoted for any destination, so it can be
    excluded before the customer has entered one. Destination and threshold
    eligibility stay server-side, where the basket and address are known.
    """
    from apps.shipping.models import ShippingMethod

    return [
        {
            "id": method.code,
            "code": method.code,
            "label": method.label,
            "description": method.description,
            "icon": {"path": method.icon_path} if method.icon_path else None,
            "requiresAreaEligibility": method.requires_area_eligibility,
            "freeOverThreshold": method.free_over_threshold,
        }
        for method in ShippingMethod.objects.filter(
            is_active=True, rates__is_active=True
        ).distinct()
    ]


def installation_offered() -> bool:
    """Is installation a service this shop currently offers at all? (T-2006)

    A *capability* flag, not an eligibility check: the checkout form is rendered
    before a governorate is chosen, so per-address eligibility cannot be known
    yet. What can be known is whether any active service covers anywhere, which
    is exactly what the approved launch state turns off.
    """
    from apps.shipping.models import InstallationService

    return InstallationService.objects.filter(
        is_active=True, governorates__isnull=False
    ).exists()


def payment_options() -> list[dict[str, Any]]:
    from apps.payments.models import PaymentMethod

    return [
        {
            "id": method.code,
            "code": method.code,
            "label": method.label,
            "description": method.description,
            "icon": {"path": method.icon_path} if method.icon_path else None,
            "notice": method.notice,
            "available": method.is_available_for_checkout,
        }
        for method in PaymentMethod.objects.filter(is_active=True)
    ]


# ---------------------------------------------------------------------------
# The client payload — presentation settings ONLY
# ---------------------------------------------------------------------------


def client_payload(setting: SiteSetting) -> dict[str, Any]:
    """The JSON handed to the browser via ``json_script``.

    Compare with the retired ``fixture_provider.get_client_fixture``, which
    shipped the entire catalogue, every review, the coupon rules and three
    prototype-state sections. Everything a script could use to compute a price,
    a discount, a VAT figure or a stock decision is gone; what stays is
    formatting metadata the UI needs to render server-supplied numbers.
    """
    return {
        "currency": {
            "code": setting.currency_code,
            "label": setting.currency_label,
            "decimalPlaces": setting.currency_decimal_places,
        },
        "locale": "ar-EG",
        "direction": "rtl",
        "maxLineQuantity": setting.max_line_quantity,
    }


# ---------------------------------------------------------------------------
# Entry points used by the views
# ---------------------------------------------------------------------------


def site_context() -> dict[str, Any]:
    """Context shared by every storefront page (header, footer, base)."""
    setting = SiteSetting.objects.get_solo()
    copy = page_copy()
    return {
        "site": build_site(setting, copy),
        "navigation": navigation(),
        "categories": published_categories(),
        "collections": published_collections(),
        "client_fixture": client_payload(setting),
        "site_setting": setting,
    }


def page_context(page: str, state: str = "default") -> dict[str, Any]:
    context = site_context()
    context.update({"page_id": page, "page_state": state})
    return context


def money(value: Decimal | int | float | None) -> str:
    """Render a money amount the way the storefront already displays it:
    zero decimal places, no thousands separator, matching the fixture output."""
    if value is None:
        return ""
    quantised = Decimal(str(value)).quantize(Decimal("1"))
    return f"{quantised}"
