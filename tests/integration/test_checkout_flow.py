"""Server-side checkout and order creation (T-1003, T-1605, FR-060 – FR-064).

The prototype's checkout was a simulation: it validated in the browser, priced
in the browser, and ended by telling the customer submission was unavailable.
These tests drive the real endpoint and assert that an ``Order`` row exists with
server-computed money, that every documented validation message is enforced
server-side, and that a replayed submission yields one order rather than two.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import Product
from apps.orders.models import Order, OrderStatus
from apps.payments.models import PaymentMethod
from apps.shipping.models import Governorate, ShippingMethod
from storefront import checkout_forms

pytestmark = pytest.mark.django_db


def _fill(**overrides):
    method = (
        ShippingMethod.objects.filter(is_active=True, requires_area_eligibility=False)
        .order_by("position")
        .first()
    )
    payment = next(
        m for m in PaymentMethod.objects.filter(is_active=True) if m.is_available_for_checkout
    )
    data = {
        "fullName": "ندى إبراهيم",
        "email": "nada@example.com",
        "mobile": "01012345678",
        "governorate": "cairo",
        "city": "القاهرة",
        "street": "١٢ شارع التحرير",
        "building": "٥",
        "shippingMethod": method.code,
        "paymentMethod": payment.code,
        "acknowledgement": "accepted",
        "idempotency_key": "test-key-0001",
    }
    data.update(overrides)
    return data


def _stock_cart(client, quantity=1):
    product = Product.objects.get(slug="zakey-apex-pro")
    variant = product.variants.first()
    client.post(
        reverse("storefront:cart-add"),
        {"variant": variant.pk, "quantity": quantity},
        follow=True,
    )
    return variant


# ---------------------------------------------------------------------------
# The happy path creates a real order
# ---------------------------------------------------------------------------


def test_checkout_creates_an_order_with_server_computed_money(storefront):
    variant = _stock_cart(storefront, 2)
    response = storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)
    assert response.status_code == 200

    order = Order.objects.get()
    assert order.status == OrderStatus.PENDING
    assert order.lines.count() == 1

    line = order.lines.get()
    assert line.quantity == 2
    # Snapshotted, not referenced: renaming the product later must not rewrite
    # what the customer bought.
    assert line.product_name == variant.product.name
    assert line.unit_price == variant.price
    assert order.subtotal == variant.price * 2
    # VAT is extracted from the gross total, never added on top.
    assert order.grand_total >= order.subtotal
    assert order.vat_amount < order.grand_total


def test_confirmation_page_shows_the_order_to_the_buyer(storefront):
    _stock_cart(storefront)
    storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)

    order = Order.objects.get()
    body = storefront.get(
        reverse("storefront:order-confirmation", kwargs={"number": order.number})
    ).content.decode()
    assert order.number in body


def test_another_visitor_cannot_read_the_order_by_number(seeded_catalogue, storefront):
    """An order number is not a lookup key for someone else's purchase."""
    from django.test import Client

    _stock_cart(storefront)
    storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)
    order = Order.objects.get()

    stranger = Client()
    response = stranger.get(
        reverse("storefront:order-confirmation", kwargs={"number": order.number})
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Idempotency (FR-064, INV-002)
# ---------------------------------------------------------------------------


def test_replaying_the_same_submission_yields_one_order(storefront):
    _stock_cart(storefront, 1)
    payload = _fill()
    storefront.post(reverse("storefront:checkout-submit"), payload, follow=True)
    for _ in range(5):
        storefront.post(reverse("storefront:checkout-submit"), payload, follow=True)

    assert Order.objects.count() == 1


def test_each_rendered_page_carries_a_fresh_idempotency_key(storefront):
    _stock_cart(storefront)
    first = storefront.get(reverse("storefront:checkout")).context["idempotency_key"]
    second = storefront.get(reverse("storefront:checkout")).context["idempotency_key"]
    assert first and second and first != second


# ---------------------------------------------------------------------------
# Every documented validation rule, enforced server-side (T-1003)
# ---------------------------------------------------------------------------


INVALID_CASES = [
    ("fullName", "A", checkout_forms.INVALID_NAME_MESSAGE),
    ("fullName", "", checkout_forms.INVALID_NAME_MESSAGE),
    ("fullName", "Nada Ibrahim", checkout_forms.INVALID_NAME_MESSAGE),  # no Arabic letter
    ("email", "not-an-email", checkout_forms.INVALID_EMAIL_MESSAGE),
    ("email", "", checkout_forms.INVALID_EMAIL_MESSAGE),
    ("mobile", "013123456789", "اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا."),
    ("mobile", "0101234", "اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا."),
    ("governorate", "", checkout_forms.REQUIRED_GOVERNORATE_MESSAGE),
    ("governorate", "atlantis", checkout_forms.REQUIRED_GOVERNORATE_MESSAGE),
    ("city", "ا", checkout_forms.INVALID_CITY_MESSAGE),
    ("street", "شار", checkout_forms.INVALID_STREET_MESSAGE),
    ("building", "", checkout_forms.REQUIRED_BUILDING_MESSAGE),
    ("shippingMethod", "", checkout_forms.REQUIRED_SHIPPING_MESSAGE),
    ("paymentMethod", "", checkout_forms.REQUIRED_PAYMENT_MESSAGE),
    ("acknowledgement", "", checkout_forms.REQUIRED_TERMS_MESSAGE),
]


@pytest.mark.parametrize("field,value,message", INVALID_CASES)
def test_invalid_field_blocks_the_order_with_the_approved_message(
    storefront, field, value, message
):
    _stock_cart(storefront)
    response = storefront.post(
        reverse("storefront:checkout-submit"), _fill(**{field: value})
    )

    assert not Order.objects.exists(), f"{field}={value!r} created an order"
    assert message in response.content.decode(), f"{field}: approved message missing"


@pytest.mark.parametrize(
    "raw", ["+201012345678", "201012345678", "٠١٠١٢٣٤٥٦٧٨", "010 1234 5678"]
)
def test_mobile_normalisation_matches_the_storefront(storefront, raw):
    """Anything the browser would have accepted is accepted here too."""
    _stock_cart(storefront)
    storefront.post(reverse("storefront:checkout-submit"), _fill(mobile=raw), follow=True)
    assert Order.objects.count() == 1
    assert Order.objects.get().phone == "01012345678"


# ---------------------------------------------------------------------------
# Money cannot be supplied by the client (FR-034, threat T-03)
# ---------------------------------------------------------------------------


def test_totals_posted_by_the_client_are_ignored(storefront):
    variant = _stock_cart(storefront, 1)
    storefront.post(
        reverse("storefront:checkout-submit"),
        _fill(
            subtotal="1",
            grand_total="1",
            discount_total="9999",
            vat_amount="0",
            shipping_total="0",
            price="1",
        ),
        follow=True,
    )

    order = Order.objects.get()
    assert order.subtotal == variant.price
    assert order.discount_total == Decimal("0.00")
    assert order.grand_total >= variant.price


def test_empty_cart_cannot_produce_an_order(storefront):
    response = storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)
    assert not Order.objects.exists()
    assert response.redirect_chain, "expected a redirect back to the cart"


def test_unavailable_payment_method_is_refused(storefront):
    """A method that is displayed but not connected must not take an order."""
    _stock_cart(storefront)
    unavailable = PaymentMethod.objects.filter(
        is_active=True, is_integrated=False, is_manual=False, collects_on_delivery=False
    ).first()
    if unavailable is None:
        pytest.skip("every seeded method is available")

    storefront.post(
        reverse("storefront:checkout-submit"), _fill(paymentMethod=unavailable.code)
    )
    assert not Order.objects.exists()


# ---------------------------------------------------------------------------
# Stock is respected (FR-061, INV-001)
# ---------------------------------------------------------------------------


def test_order_reserves_stock(storefront):
    variant = _stock_cart(storefront, 2)
    before = variant.stock_item.reserved

    storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)

    variant.stock_item.refresh_from_db()
    assert variant.stock_item.reserved == before + 2


def test_cart_is_converted_and_no_longer_active(storefront):
    from apps.cart.models import Cart, CartStatus

    _stock_cart(storefront)
    storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)

    assert Cart.objects.get().status == CartStatus.CONVERTED
    # …and the checkout page now reports an empty basket rather than re-offering
    # the converted one.
    assert not storefront.get(reverse("storefront:checkout")).context["cart_lines"]


def test_same_day_method_refused_for_an_ineligible_area(storefront):
    method = ShippingMethod.objects.filter(
        is_active=True, requires_area_eligibility=True
    ).first()
    if method is None:
        pytest.skip("no eligibility-gated shipping method seeded")

    _stock_cart(storefront)
    storefront.post(
        reverse("storefront:checkout-submit"),
        _fill(shippingMethod=method.code, areaKey=""),
    )
    assert not Order.objects.exists()


def test_checkout_endpoint_rejects_get(storefront):
    assert storefront.get(reverse("storefront:checkout-submit")).status_code == 405


def test_checkout_requires_csrf(seeded_catalogue):
    from django.test import Client

    unsafe = Client(enforce_csrf_checks=True)
    assert unsafe.post(reverse("storefront:checkout-submit"), {}).status_code == 403


def test_governorate_without_a_shipping_rate_is_refused(storefront):
    """Not every governorate is served; the server must say so rather than
    quoting zero and taking the order."""
    _stock_cart(storefront)

    # The seed puts every governorate in one zone, so an unserved destination
    # has to be *created* rather than found. Skipping instead would have left
    # the "quote or refuse" branch untested precisely because the demo data is
    # generous — the coverage would disappear the moment it mattered least.
    unserved = Governorate.objects.create(
        key="test-unserved", name="محافظة بلا تغطية", position=99
    )

    response = storefront.post(
        reverse("storefront:checkout-submit"), _fill(governorate=unserved.key)
    )

    assert not Order.objects.exists()
    assert "لا توجد تسعيرة شحن لهذه المحافظة." in response.content.decode()


# ---------------------------------------------------------------------------
# Free shipping, installation and the terms control (FR-046, FR-062, FR-063)
#
# The seeded shipping and installation money is development placeholder data
# (ASM-004, ASM-005) and the commercial figures are still an open business
# decision (T-2006). Every amount the tests below write is therefore an
# obviously fake number kept behind ``is_placeholder=True`` — enough to tell
# "charged" from "free", and impossible to mistake for an approved price.
# ---------------------------------------------------------------------------

FAKE_RATE = Decimal("11.00")
FAKE_INSTALLATION_FEE = Decimal("22.00")


def _fake_free_over_threshold_method():
    """The seeded free-shipping method, priced with a fake development rate.

    Its seeded placeholder is 0.00, which would make "free" and "charged"
    indistinguishable and the assertion below vacuous.
    """
    from apps.shipping.models import ShippingMethod, ShippingRate

    method = ShippingMethod.objects.get(code="shipping-free")
    assert method.free_over_threshold is True
    ShippingRate.objects.filter(method=method).update(
        price=FAKE_RATE, is_placeholder=True, is_active=True
    )
    return method


def _set_threshold(amount: Decimal) -> Decimal:
    from apps.core.models import SiteSetting

    settings_obj = SiteSetting.objects.get_solo()
    settings_obj.free_shipping_threshold = amount
    settings_obj.save(update_fields=["free_shipping_threshold"])
    return amount


def test_free_shipping_applies_when_the_basket_reaches_the_configured_threshold(storefront):
    """FR-046: at or above the configured threshold the customer pays no shipping."""
    method = _fake_free_over_threshold_method()
    variant = _stock_cart(storefront, 1)
    threshold = _set_threshold((variant.price * Decimal("0.75")).quantize(Decimal("0.01")))

    storefront.post(
        reverse("storefront:checkout-submit"),
        _fill(shippingMethod=method.code),
        follow=True,
    )

    order = Order.objects.get()
    assert order.subtotal >= threshold
    assert order.discount_total == Decimal("0.00")
    assert order.shipping_total == Decimal("0.00")


def test_a_discount_that_drops_the_basket_below_the_threshold_restores_the_charge(storefront):
    """FR-046: the threshold is tested against the subtotal *after* the discount.

    The gross subtotal clears the threshold on its own here, so shipping can
    only come back if the discount is subtracted first. Checking the gross
    figure would give this cart free delivery it did not earn.
    """
    from apps.cart.models import Cart, CartStatus
    from apps.promotions.models import Coupon, DiscountType

    method = _fake_free_over_threshold_method()
    variant = _stock_cart(storefront, 1)
    threshold = _set_threshold((variant.price * Decimal("0.75")).quantize(Decimal("0.01")))

    coupon = Coupon.objects.create(
        code="FR046HALFOFF",
        discount_type=DiscountType.PERCENTAGE,
        value=Decimal("50.00"),
        is_demo=True,
    )
    basket = Cart.objects.get(status=CartStatus.ACTIVE)
    basket.coupon = coupon
    basket.save(update_fields=["coupon", "updated_at"])

    storefront.post(
        reverse("storefront:checkout-submit"),
        _fill(shippingMethod=method.code),
        follow=True,
    )

    order = Order.objects.get()
    assert order.subtotal >= threshold, "the gross subtotal alone would have qualified"
    assert order.discount_total > Decimal("0.00")
    assert order.subtotal - order.discount_total < threshold
    assert order.shipping_total == FAKE_RATE


def test_the_installation_fee_is_added_to_the_total_and_shown_as_a_summary_row(storefront):
    """FR-062: the fee lands in the grand total and appears as its own row.

    Two identical baskets are checked out, one asking for installation and one
    not. The whole difference between the two totals is the fee, which is what
    "added to the order total" has to mean; and the confirmation summary gains
    one row rather than folding the money silently into another line.
    """
    from django.template.defaultfilters import floatformat
    from django.test import Client

    from apps.shipping.models import InstallationService

    InstallationService.objects.filter(is_active=True).update(
        fee=FAKE_INSTALLATION_FEE, is_placeholder=True
    )

    _stock_cart(storefront, 1)
    storefront.post(
        reverse("storefront:checkout-submit"),
        _fill(installation="requested"),
        follow=True,
    )
    with_installation = Order.objects.get()

    plain_visitor = Client()
    _stock_cart(plain_visitor, 1)
    plain_visitor.post(
        reverse("storefront:checkout-submit"),
        _fill(idempotency_key="test-key-0002"),
        follow=True,
    )
    without = Order.objects.exclude(pk=with_installation.pk).get()

    assert with_installation.installation_requested is True
    assert with_installation.installation_total == FAKE_INSTALLATION_FEE
    assert without.installation_requested is False
    assert without.installation_total == Decimal("0.00")
    assert with_installation.subtotal == without.subtotal
    assert (
        with_installation.grand_total - without.grand_total == FAKE_INSTALLATION_FEE
    ), "the fee must be added to the total, not absorbed by it"
    # An order priced on unapproved development money says so (T-2006).
    assert with_installation.used_placeholder_rates is True

    body = storefront.get(
        reverse("storefront:order-confirmation", kwargs={"number": with_installation.number})
    ).content.decode()
    assert (
        f"<dt>التركيب</dt><dd>{floatformat(FAKE_INSTALLATION_FEE, 0)} ج.م</dd>" in body
    ), "the summary must show installation as its own row"


def test_the_acknowledgement_keeps_its_control_position_and_styling(storefront):
    """FR-063: the same checkbox, in the same place, wearing the same classes.

    The approved storefront is a protected surface: this requirement changes
    the *meaning* of the control and its label, and nothing else. So the test
    pins the parts that must not move — the element, its name, its id, its
    classes and its position between the payment review and the confirm button
    — rather than merely checking that some checkbox exists somewhere.
    """
    _stock_cart(storefront)
    page = storefront.get(reverse("storefront:checkout")).content.decode()

    assert 'class="checkout-check-row checkout-acknowledgement"' in page

    start = page.index('<input type="checkbox" id="checkout-acknowledgement"')
    control = page[start : page.index(">", start) + 1]
    assert 'name="acknowledgement"' in control
    assert 'value="accepted"' in control
    assert "required" in control
    assert 'aria-describedby="checkout-acknowledgement-error"' in control

    assert (
        page.index("data-review-payment")
        < page.index('id="checkout-acknowledgement"')
        < page.index("data-checkout-final")
    ), "the control must stay between the payment review and the confirm button"


def test_the_label_now_asks_for_terms_acceptance_rather_than_prototype_awareness(storefront):
    """FR-063: the label is what changed — it asks for consent, not awareness.

    The prototype's checkbox confirmed the visitor understood the demo was not
    a shop ("أكد فهمك أن هذه واجهة تجريبية"). The button now creates a real
    order, so the same control has to ask for something real.
    """
    _stock_cart(storefront)
    page = storefront.get(reverse("storefront:checkout")).content.decode()

    start = page.index('class="checkout-check-row checkout-acknowledgement"')
    label = page[start : page.index("</label>", start)]

    assert "أوافق على الشروط والأحكام" in label
    assert "واجهة تجريبية" not in label
    assert checkout_forms.REQUIRED_TERMS_MESSAGE == "أكد موافقتك على الشروط لإتمام الطلب."


def test_accepting_the_terms_is_recorded_on_the_order(storefront):
    """FR-063: acceptance is stored, not merely required.

    A consent that leaves no trace cannot be produced later, when it is the
    only thing that matters.
    """
    _stock_cart(storefront)
    storefront.post(reverse("storefront:checkout-submit"), _fill(), follow=True)

    order = Order.objects.get()
    assert order.terms_accepted_at is not None
    assert order.terms_accepted_at <= order.placed_at


def test_an_order_cannot_be_placed_without_accepting_the_terms(storefront):
    """FR-063: the box is a gate, and the refusal names the terms."""
    _stock_cart(storefront)
    response = storefront.post(
        reverse("storefront:checkout-submit"), _fill(acknowledgement="")
    )

    assert not Order.objects.exists()
    assert checkout_forms.REQUIRED_TERMS_MESSAGE in response.content.decode()
