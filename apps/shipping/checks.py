"""Startup validation of the commercial configuration (T-2006, ASM-004, ASM-005).

The launch decision is an **intentional disabled-service state**, not a set of
missing values:

* shipping is free for eligible orders at or above the approved threshold;
* no paid shipping rate is offered below it;
* installation is switched off, with no active governorate and no active fee.

That state is *approved*, so production must start cleanly in it. What production
must still refuse is the other thing that looks similar from a distance — an
active **placeholder** rate, i.e. a development number nobody signed off, quietly
being charged to a customer.

These checks make the difference explicit at startup rather than at the moment a
customer is quoted a price. They are deliberately tolerant of an unmigrated or
unreachable database: `manage.py check` legitimately runs before `migrate` in a
fresh deploy, and a check that crashes there would block the very command that
fixes it.
"""

from __future__ import annotations

from django.conf import settings
from django.core.checks import Error, Warning, register
from django.db import DatabaseError

#: Stable ids so a deployment log can be grepped for exactly one condition.
PLACEHOLDER_SHIPPING = "zakey.shipping.E001"
PLACEHOLDER_INSTALLATION = "zakey.shipping.E002"
PAID_BELOW_THRESHOLD = "zakey.shipping.W001"


def _allows_placeholders() -> bool:
    return bool(getattr(settings, "ZAKEY_ALLOW_PLACEHOLDER_RATES", False))


@register()
def commercial_rates_are_approved(app_configs, **kwargs):
    """Refuse to start production with an unapproved price switched on."""
    if _allows_placeholders():
        # Development and test deliberately run on placeholders.
        return []

    from .models import InstallationService, ShippingRate

    try:
        bad_rates = list(
            ShippingRate.objects.filter(is_active=True, is_placeholder=True)
            .select_related("method")[:10]
        )
        bad_services = list(
            InstallationService.objects.filter(is_active=True, is_placeholder=True)[:10]
        )
    except DatabaseError:
        # Not migrated yet, or no database on this host. `migrate` will run and
        # this check will have something real to look at next time.
        return []

    problems = []
    if bad_rates:
        named = "، ".join(f"{r.method.label}" for r in bad_rates)
        problems.append(
            Error(
                "أسعار شحن تطويرية غير معتمدة ما زالت مفعّلة في بيئة الإنتاج.",
                hint=(
                    "Active shipping rates are still flagged is_placeholder. "
                    f"Methods: {named}. Enter the approved rates in the admin, or "
                    "deactivate them. Never set ZAKEY_ALLOW_PLACEHOLDER_RATES=1 in "
                    "production to silence this."
                ),
                id=PLACEHOLDER_SHIPPING,
            )
        )
    if bad_services:
        problems.append(
            Error(
                "رسوم تركيب تطويرية غير معتمدة ما زالت مفعّلة في بيئة الإنتاج.",
                hint=(
                    "An active InstallationService is still flagged is_placeholder. "
                    "Enter the approved fee, or deactivate the service — the "
                    "approved launch state has installation switched off."
                ),
                id=PLACEHOLDER_INSTALLATION,
            )
        )
    return problems


@register()
def paid_shipping_matches_the_launch_policy(app_configs, **kwargs):
    """Flag a paid rate that would be charged below the free threshold.

    Not an error: enabling paid shipping later is an approved, expected workflow.
    It is a warning so that turning it on is a visible, deliberate act in the
    deployment log rather than something noticed from a customer complaint.
    """
    if _allows_placeholders():
        return []

    from .models import ShippingRate

    try:
        paid = list(
            ShippingRate.objects.filter(
                is_active=True, free_threshold_only=False, is_placeholder=False
            )
            .exclude(price=0)
            .select_related("method")[:10]
        )
    except DatabaseError:
        return []

    if not paid:
        return []

    named = "، ".join(f"{r.method.label} ({r.price})" for r in paid)
    return [
        Warning(
            "توجد أسعار شحن مدفوعة مفعّلة — تأكد أنها معتمدة تجاريًا.",
            hint=(
                "The approved launch policy offers free shipping above the "
                f"threshold only. Active paid rates: {named}. This is expected "
                "once paid shipping has been approved and entered; it is a "
                "warning so the change is visible in the deploy log."
            ),
            id=PAID_BELOW_THRESHOLD,
        )
    ]
