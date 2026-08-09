"""Create the nine staff roles as Django groups (FR-110, FR-111).

Idempotent: re-running reconciles permissions rather than duplicating groups.

Permissions are enforced server-side by Django. Jazzmin menu visibility follows
them but is never the boundary — hiding a link grants nothing and denies nothing
(``permissions-matrix.md`` §4).
"""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

VIEW, ADD, CHANGE, DELETE = "view", "add", "change", "delete"
ALL = (VIEW, ADD, CHANGE, DELETE)
RW = (VIEW, ADD, CHANGE)
RO = (VIEW,)

#: role -> {"app_label.modelname": (actions,)}
ROLES: dict[str, dict[str, tuple[str, ...]]] = {
    "Super Administrator": {"*": ALL},
    "Store Manager": {
        "catalog.product": ALL, "catalog.productvariant": ALL, "catalog.category": ALL,
        "catalog.collection": ALL, "catalog.brand": ALL, "catalog.productimage": ALL,
        "inventory.stockitem": RW, "inventory.stockmovement": RO, "inventory.stockreservation": RO,
        "orders.order": RW, "orders.orderline": RO, "orders.orderevent": RO, "orders.ordernote": RW,
        "payments.payment": RW, "payments.refund": (VIEW, ADD), "payments.paymentmethod": RW,
        "accounts.customerprofile": RW, "accounts.address": RW,
        "shipping.shippingrate": ALL, "shipping.shippingmethod": ALL, "shipping.shippingzone": ALL,
        "shipping.installationservice": ALL, "shipping.governorate": RW, "shipping.servicearea": RW,
        "promotions.coupon": ALL, "promotions.couponredemption": RO,
        "reviews.review": ALL, "content.faq": RW, "content.homesection": RW,
        "content.banner": RW, "content.staticpage": RW, "content.navigationitem": RW,
        "core.sitesetting": RW, "audit.auditlog": RO,
    },
    "Catalogue Manager": {
        "catalog.product": ALL, "catalog.productvariant": ALL, "catalog.productimage": ALL,
        "catalog.productfeature": ALL, "catalog.productdocument": ALL,
        "catalog.specificationgroup": ALL, "catalog.specificationitem": ALL,
        "catalog.category": ALL, "catalog.collection": ALL, "catalog.brand": ALL,
        "inventory.stockitem": RO, "promotions.coupon": RW, "reviews.review": RW,
    },
    "Inventory Manager": {
        "inventory.stockitem": RW, "inventory.stockmovement": (VIEW, ADD),
        "inventory.stockreservation": RO,
        "catalog.product": RO, "catalog.productvariant": RO, "orders.order": RO,
    },
    "Order Fulfilment": {
        "orders.order": (VIEW, CHANGE), "orders.orderline": RO, "orders.orderevent": RO,
        "orders.ordernote": (VIEW, ADD), "orders.orderaddress": (VIEW, CHANGE),
        "inventory.stockitem": RO, "inventory.stockreservation": RO,
        "catalog.product": RO, "accounts.customerprofile": RO, "accounts.address": RO,
        "shipping.shippingmethod": RO, "shipping.governorate": RO, "shipping.servicearea": RO,
    },
    "Customer Service": {
        "orders.order": (VIEW, CHANGE), "orders.orderline": RO, "orders.orderevent": RO,
        "orders.ordernote": (VIEW, ADD), "orders.orderaddress": (VIEW, CHANGE),
        "accounts.customerprofile": RW, "accounts.address": RW, "accounts.user": RO,
        "catalog.product": RO, "reviews.review": RW, "content.contactmessage": RW,
        "promotions.coupon": RO, "promotions.couponredemption": RO, "payments.payment": RO,
    },
    "Finance": {
        "payments.payment": RW, "payments.refund": RW, "payments.paymentevent": RO,
        "payments.paymentmethod": RW,
        "orders.order": (VIEW, CHANGE), "orders.orderline": RO, "orders.orderevent": RO,
        "promotions.coupon": RO, "promotions.couponredemption": RO,
        "inventory.stockitem": RO, "inventory.stockmovement": RO,
        "accounts.customerprofile": RO, "audit.auditlog": RO,
        "shipping.shippingrate": RO, "shipping.installationservice": RO,
    },
    "Content Manager": {
        "content.homesection": ALL, "content.banner": ALL, "content.partner": ALL,
        "content.faq": ALL, "content.staticpage": ALL, "content.navigationitem": ALL,
        "content.newslettersubscription": RW, "content.contactmessage": RW,
        "core.sitesetting": RW, "reviews.review": RW,
        "catalog.product": RO, "catalog.category": RO, "catalog.collection": RO,
    },
    # Reads everything, changes nothing - anywhere.
    "Read-only Auditor": {"*": RO},
}


class Command(BaseCommand):
    help = "Create or reconcile the nine ZAKEY staff roles (idempotent)."

    @transaction.atomic
    def handle(self, *args, **options):
        all_permissions = list(
            Permission.objects.select_related("content_type").all()
        )
        by_key: dict[str, list[Permission]] = {}
        for permission in all_permissions:
            key = f"{permission.content_type.app_label}.{permission.content_type.model}"
            by_key.setdefault(key, []).append(permission)

        for role_name, spec in ROLES.items():
            group, created = Group.objects.get_or_create(name=role_name)
            granted: list[Permission] = []

            if "*" in spec:
                actions = spec["*"]
                for permission in all_permissions:
                    # Never grant Django's own admin/session plumbing wholesale.
                    if permission.content_type.app_label in {"admin", "sessions", "contenttypes"}:
                        continue
                    if permission.codename.split("_", 1)[0] in actions:
                        granted.append(permission)
            else:
                for model_key, actions in spec.items():
                    for permission in by_key.get(model_key, []):
                        if permission.codename.split("_", 1)[0] in actions:
                            granted.append(permission)

            group.permissions.set(granted)
            self.stdout.write(
                f"  {'created' if created else 'updated'}  {role_name:<22} "
                f"{len(granted)} permission(s)"
            )

        self.stdout.write(self.style.SUCCESS(f"\n{len(ROLES)} roles reconciled."))
        self.stdout.write(
            "AuditLog, StockMovement, PaymentEvent and OrderEvent expose no add/change/"
            "delete path in the admin, so no role can mutate them (INV-013)."
        )
