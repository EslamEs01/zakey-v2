"""What an order remembers about itself (FR-066, INV-003).

An order is a record of what was agreed, not a view onto the current catalogue.
Every figure and every label the customer saw is copied onto the order at
creation, so the order still reads correctly after the product is renamed, the
price changes, the coupon is withdrawn, the shipping method is relabelled and
the governorate is spelled differently.

The two tests below split that into its two halves: everything the requirement
enumerates is *written*, and none of it moves afterwards when its source does.

Every shipping and installation amount here is a deliberately fake development
value carried with ``is_placeholder=True``: the real numbers are business input
that does not exist yet (T-2006), and inventing one in a test is how an
unapproved figure ends up looking approved.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.cart.services import add_to_cart, get_or_create_cart
from apps.core.money import extract_vat
from apps.orders.services import create_order
from apps.promotions.models import Coupon, DiscountType

pytestmark = pytest.mark.django_db

ADDRESS = {
    "full_name": "ندى إبراهيم",
    "phone": "01098765432",
    "governorate_key": "cairo",
    "governorate_name": "القاهرة",
    "area_key": "cairo-nasr-city",
    "area_name": "مدينة نصر",
    "city": "القاهرة",
    "street": "١٢ شارع التحرير",
    "building": "٥",
    "landmark": "بجوار الصيدلية",
}

#: Obviously fake development money. Not a quote, not a proposal, not a price.
FAKE_SHIPPING = Decimal("11.00")
FAKE_SHIPPING_LABEL = "شحن تطويري (قيمة غير معتمدة)"
FAKE_INSTALLATION = Decimal("22.00")


@pytest.fixture
def placed_order(variant, stock, site_setting, customer):
    """One order carrying every component FR-066 enumerates."""
    coupon = Coupon.objects.create(
        code="FR066TENTH",
        discount_type=DiscountType.PERCENTAGE,
        value=Decimal("10.00"),
        is_demo=True,
    )
    cart = get_or_create_cart(customer=customer)
    add_to_cart(cart, variant, 2)
    cart.coupon = coupon
    cart.save(update_fields=["coupon", "updated_at"])

    return create_order(
        cart=cart,
        email="Nada@Example.com",
        phone="01098765432",
        address_data=dict(ADDRESS),
        idempotency_key="fr066-key",
        shipping_quote=(FAKE_SHIPPING, FAKE_SHIPPING_LABEL, True),
        installation_quote=(FAKE_INSTALLATION, True),
        customer=customer,
        terms_accepted=True,
    )


def test_the_order_stores_every_component_the_customer_agreed_to(
    placed_order, variant, site_setting
):
    """FR-066: line, address, contact, VAT, discount, coupon, shipping,
    installation and grand total are all present on the order itself.

    Each assertion names one item from the requirement's list, so a component
    that stops being snapshotted fails here by name rather than by a mismatched
    total somewhere downstream.
    """
    order = placed_order

    # line: product name, variant, SKU, unit price, quantity, line total
    line = order.lines.get()
    assert line.product_name == variant.product.name
    assert line.variant_label == variant.finish_label
    assert line.sku == variant.sku
    assert line.unit_price == variant.price
    assert line.quantity == 2
    assert line.line_total == variant.price * 2

    # address
    address = order.address
    for field, expected in ADDRESS.items():
        assert getattr(address, field) == expected, field

    # customer contact
    assert order.email == "nada@example.com"
    assert order.phone == "01098765432"

    # discount and coupon code
    assert order.coupon_code == "FR066TENTH"
    assert order.discount_total == (variant.price * 2 * Decimal("0.10")).quantize(
        Decimal("0.01")
    )

    # shipping method and cost
    assert order.shipping_method_label == FAKE_SHIPPING_LABEL
    assert order.shipping_total == FAKE_SHIPPING

    # installation and cost
    assert order.installation_requested is True
    assert order.installation_total == FAKE_INSTALLATION

    # grand total, and the VAT extracted from it at the rate of the day
    assert order.grand_total == (
        order.subtotal - order.discount_total + order.shipping_total + order.installation_total
    )
    assert order.vat_rate == site_setting.vat_rate
    assert order.vat_amount == extract_vat(order.grand_total, site_setting.vat_rate)

    # …and the audit flag that says this order was priced on unapproved
    # development rates, so it can never be mistaken for a commercial one.
    assert order.used_placeholder_rates is True


def test_none_of_it_moves_when_the_sources_move(placed_order, variant, site_setting):
    """FR-066: the snapshot is immutable in the only way that matters — it does
    not follow the rows it was copied from.

    The catalogue is renamed and repriced, the tax rate is changed and the
    coupon is renamed, revalued and switched off. An order that read through
    foreign keys would now show a different price, a different name, a
    different tax and a coupon code the customer never typed.
    """
    order = placed_order
    before = {
        "product_name": order.lines.get().product_name,
        "unit_price": order.lines.get().unit_price,
        "line_total": order.lines.get().line_total,
        "subtotal": order.subtotal,
        "discount_total": order.discount_total,
        "coupon_code": order.coupon_code,
        "shipping_total": order.shipping_total,
        "installation_total": order.installation_total,
        "vat_amount": order.vat_amount,
        "vat_rate": order.vat_rate,
        "grand_total": order.grand_total,
        "governorate_name": order.address.governorate_name,
    }

    variant.product.name = "اسم مختلف تمامًا"
    variant.product.save(update_fields=["name"])
    variant.price = Decimal("1.00")
    variant.save(update_fields=["price"])
    site_setting.vat_rate = Decimal("0.2000")
    site_setting.save(update_fields=["vat_rate"])
    Coupon.objects.filter(code="FR066TENTH").update(
        code="FR066RENAMED", value=Decimal("90.00"), is_active=False
    )

    order.refresh_from_db()
    line = order.lines.get()
    line.refresh_from_db()
    order.address.refresh_from_db()

    assert line.product_name == before["product_name"]
    assert line.unit_price == before["unit_price"]
    assert line.line_total == before["line_total"]
    assert order.subtotal == before["subtotal"]
    assert order.discount_total == before["discount_total"]
    assert order.coupon_code == before["coupon_code"]
    assert order.shipping_total == before["shipping_total"]
    assert order.installation_total == before["installation_total"]
    assert order.vat_amount == before["vat_amount"]
    assert order.vat_rate == before["vat_rate"]
    assert order.grand_total == before["grand_total"]
    assert order.address.governorate_name == before["governorate_name"]

    # And the snapshot cannot be rewritten in place either.
    line.unit_price = Decimal("1.00")
    with pytest.raises(ValidationError):
        line.save()
