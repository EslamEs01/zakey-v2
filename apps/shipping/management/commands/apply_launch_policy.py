"""Apply the approved commercial launch policy (T-2006, ASM-004, ASM-005).

The approved decision is a **disabled-service launch**, not a set of placeholders
waiting to be filled:

* currency EGP, VAT 14% (already configured, untouched here);
* free shipping for eligible orders **at or above EGP 1,500**;
* **no paid shipping** method or zone rate offered below the threshold;
* **installation switched off** — no active fee, no eligible governorate;
* effective from the deployment date.

Running this turns the seeded development placeholders into that approved state.
It is idempotent, so it is safe in a deploy script and safe to re-run after a
seed. Enabling paid shipping or installation later is deliberately **not** this
command's job: that needs approved figures entered through the admin, which is
audited per object.

    uv run python manage.py apply_launch_policy [--dry-run]
"""

from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

FREE_METHOD_NOTE = "الشحن مجاني للطلبات المؤهلة من 1500 ج.م فأكثر."


class Command(BaseCommand):
    help = "Apply the approved disabled-service launch policy for shipping and installation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report what would change without writing anything.",
        )
        parser.add_argument(
            "--actor",
            default="",
            help="Email of the staff member accountable for applying the policy.",
        )

    def handle(self, *args, **options):
        from apps.core.models import SiteSetting
        from apps.shipping.models import InstallationService, ShippingRate

        dry_run = options["dry_run"]
        changes: list[str] = []

        with transaction.atomic():
            settings_row = SiteSetting.objects.get_solo()
            threshold = settings_row.free_shipping_threshold

            free_rates = ShippingRate.objects.filter(method__free_over_threshold=True)
            paid_rates = ShippingRate.objects.filter(method__free_over_threshold=False)

            # 1. The free-above-threshold rate becomes approved, zero, and
            #    offered only when the threshold is met.
            for rate in free_rates:
                if (
                    rate.price == Decimal("0.00")
                    and rate.is_placeholder is False
                    and rate.free_threshold_only
                    and rate.is_active
                ):
                    continue
                changes.append(
                    f"free rate «{rate.method.label}»: price=0.00, approved, "
                    f"free_threshold_only=True, active"
                )
                if not dry_run:
                    rate.price = Decimal("0.00")
                    rate.is_placeholder = False
                    rate.free_threshold_only = True
                    rate.is_active = True
                    rate.estimated_delivery_text = (
                        rate.estimated_delivery_text or FREE_METHOD_NOTE
                    )
                    rate.save(
                        update_fields=[
                            "price",
                            "is_placeholder",
                            "free_threshold_only",
                            "is_active",
                            "estimated_delivery_text",
                            "updated_at",
                        ]
                    )

            # 2. Every paid rate is withdrawn. Deactivated rather than deleted:
            #    the row is the record of what was configured, and re-enabling it
            #    later must be a deliberate edit with an approved figure.
            for rate in paid_rates.filter(is_active=True):
                changes.append(f"paid rate «{rate.method.label}»: deactivated")
                if not dry_run:
                    rate.is_active = False
                    rate.save(update_fields=["is_active", "updated_at"])

            # 3. Installation is switched off entirely.
            for service in InstallationService.objects.all():
                needs = service.is_active or service.governorates.exists()
                if not needs:
                    continue
                changes.append(f"installation «{service.name}»: deactivated, governorates cleared")
                if not dry_run:
                    service.is_active = False
                    service.save(update_fields=["is_active", "updated_at"])
                    service.governorates.clear()

            if not dry_run and changes:
                self._audit(options.get("actor") or "", settings_row, threshold, changes)

        verb = "would change" if dry_run else "changed"
        if not changes:
            self.stdout.write(self.style.SUCCESS("launch policy already applied; nothing to do"))
        else:
            for line in changes:
                self.stdout.write(f"  {verb}: {line}")

        self.stdout.write("")
        self.stdout.write(f"free shipping threshold : {threshold} EGP")
        self.stdout.write(f"paid shipping           : not offered at launch")
        self.stdout.write(f"installation            : disabled at launch")
        self.stdout.write(f"effective               : {timezone.now().date().isoformat()}")

        from apps.shipping.services import has_unapproved_rates

        if has_unapproved_rates():
            self.stdout.write(
                self.style.ERROR("STILL UNAPPROVED: an active placeholder rate remains")
            )
            return
        self.stdout.write(self.style.SUCCESS("no active placeholder rate remains"))

    def _audit(self, actor_email: str, settings_row, threshold, changes: list[str]) -> None:
        """Record who applied the policy and exactly what it changed.

        Attributed to the site-settings row so the entry appears against a real
        object in the admin's audit view rather than as a floating note.
        """
        from apps.audit.models import AuditAction
        from apps.audit.services import record_audit

        actor = None
        if actor_email:
            from apps.accounts.models import User

            actor = User.objects.filter(email=actor_email).first()

        record_audit(
            actor=actor,
            action=AuditAction.UPDATE,
            obj=settings_row,
            changes={
                "commercial_policy": "launch",
                "free_shipping_threshold": str(threshold),
                "paid_shipping": "withdrawn",
                "installation": "disabled",
                "applied": changes,
                "actor_email": actor_email or "unattributed",
            },
        )
