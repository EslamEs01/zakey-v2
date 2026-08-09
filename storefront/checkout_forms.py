"""Server-side checkout validation (T-1003, T-1605, FR-060, FR-063).

Every rule and every Arabic message below is the one the prototype enforced in
the browser (`frontend-contract.md` §4). They are reproduced here because
client-side validation is a convenience, not a control: the only check that
counts is the one an attacker cannot skip by posting directly.

Money is conspicuously absent. The form collects an address, a shipping method
and a payment method — the totals are computed by
``apps.cart.services.price_cart`` and ``apps.orders.services.create_order``
from database rows.
"""

from __future__ import annotations

import re

from django import forms

from apps.accounts.validators import (
    INVALID_MOBILE_MESSAGE,
    normalize_egyptian_mobile,
    validate_egyptian_mobile,
)
from apps.payments.models import PaymentMethod
from apps.shipping.models import Governorate, ServiceArea, ShippingMethod

#: An Arabic letter anywhere in the value (checkout.js full-name rule).
ARABIC_LETTER_RE = re.compile(r"[؀-ۿ]")

INVALID_NAME_MESSAGE = "اكتب الاسم بالكامل بالعربية."
INVALID_EMAIL_MESSAGE = "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com."
REQUIRED_GOVERNORATE_MESSAGE = "اختر المحافظة."
INVALID_CITY_MESSAGE = "اكتب اسم المدينة أو المركز."
INVALID_STREET_MESSAGE = "اكتب اسم الشارع والعنوان التفصيلي."
REQUIRED_BUILDING_MESSAGE = "اكتب رقم المبنى."
REQUIRED_SHIPPING_MESSAGE = "اختر طريقة الشحن."
REQUIRED_PAYMENT_MESSAGE = "اختر طريقة الدفع."
#: FR-063: the prototype's "this is a demo" acknowledgement becomes real terms
#: acceptance now that the button creates an order.
REQUIRED_TERMS_MESSAGE = "أكد موافقتك على الشروط لإتمام الطلب."


class CheckoutForm(forms.Form):
    """One form for the whole checkout.

    The storefront presents three steps, but a step is a *presentation* device:
    the server validates the complete submission at once, so skipping ahead by
    posting to the final endpoint cannot bypass step one's rules.
    """

    fullName = forms.CharField(required=False)
    email = forms.CharField(required=False)
    mobile = forms.CharField(required=False)
    governorate = forms.CharField(required=False)
    city = forms.CharField(required=False)
    areaKey = forms.CharField(required=False)
    street = forms.CharField(required=False)
    building = forms.CharField(required=False)
    landmark = forms.CharField(required=False, max_length=100)
    shippingMethod = forms.CharField(required=False)
    paymentMethod = forms.CharField(required=False)
    installation = forms.CharField(required=False)
    acknowledgement = forms.CharField(required=False)

    def clean_fullName(self):
        value = (self.cleaned_data.get("fullName") or "").strip()
        if len(value) < 2 or not ARABIC_LETTER_RE.search(value):
            raise forms.ValidationError(INVALID_NAME_MESSAGE)
        return value

    def clean_email(self):
        value = (self.cleaned_data.get("email") or "").strip()
        # The storefront's own regex, not Django's stricter EmailValidator, so
        # an address accepted in the browser is accepted here too.
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", value):
            raise forms.ValidationError(INVALID_EMAIL_MESSAGE)
        return value.lower()

    def clean_mobile(self):
        value = (self.cleaned_data.get("mobile") or "").strip()
        validate_egyptian_mobile(value)
        return normalize_egyptian_mobile(value)

    def clean_governorate(self):
        key = (self.cleaned_data.get("governorate") or "").strip()
        governorate = Governorate.objects.filter(key=key, is_active=True).first()
        if governorate is None:
            raise forms.ValidationError(REQUIRED_GOVERNORATE_MESSAGE)
        return governorate

    def clean_city(self):
        value = (self.cleaned_data.get("city") or "").strip()
        if len(value) < 2:
            raise forms.ValidationError(INVALID_CITY_MESSAGE)
        return value

    def clean_street(self):
        value = (self.cleaned_data.get("street") or "").strip()
        if len(value) < 4:
            raise forms.ValidationError(INVALID_STREET_MESSAGE)
        return value

    def clean_building(self):
        value = (self.cleaned_data.get("building") or "").strip()
        if not value:
            raise forms.ValidationError(REQUIRED_BUILDING_MESSAGE)
        return value

    def clean_shippingMethod(self):
        code = (self.cleaned_data.get("shippingMethod") or "").strip()
        method = ShippingMethod.objects.filter(code=code, is_active=True).first()
        if method is None:
            raise forms.ValidationError(REQUIRED_SHIPPING_MESSAGE)
        return method

    def clean_paymentMethod(self):
        code = (self.cleaned_data.get("paymentMethod") or "").strip()
        method = PaymentMethod.objects.filter(code=code, is_active=True).first()
        if method is None:
            raise forms.ValidationError(REQUIRED_PAYMENT_MESSAGE)
        if not method.is_available_for_checkout:
            # Displayed but not connected to any provider (FR-072): offering it
            # and then failing at capture would be worse than refusing now.
            raise forms.ValidationError("طريقة الدفع هذه غير متاحة حاليًا.")
        return method

    def clean_acknowledgement(self):
        if not (self.cleaned_data.get("acknowledgement") or "").strip():
            raise forms.ValidationError(REQUIRED_TERMS_MESSAGE)
        return True

    def clean(self):
        cleaned = super().clean()
        governorate = cleaned.get("governorate")
        area_key = (cleaned.get("areaKey") or "").strip()

        area = None
        if area_key and governorate is not None:
            area = ServiceArea.objects.filter(
                key=area_key, governorate=governorate, is_active=True
            ).first()
            if area is None:
                # A mismatched area is dropped rather than rejected: it is
                # optional, and the address is still deliverable without it.
                area_key = ""
        cleaned["area"] = area

        method = cleaned.get("shippingMethod")
        if method is not None and method.requires_area_eligibility:
            if area is None or not area.same_day_eligible:
                self.add_error(
                    "shippingMethod", "هذه الطريقة غير متاحة للمنطقة المختارة."
                )
        return cleaned

    # -- output ------------------------------------------------------------

    def address_data(self) -> dict:
        """The immutable address snapshot stored on the order (INV-003)."""
        governorate = self.cleaned_data["governorate"]
        area = self.cleaned_data.get("area")
        return {
            "full_name": self.cleaned_data["fullName"],
            "phone": self.cleaned_data["mobile"],
            "governorate_key": governorate.key,
            "governorate_name": governorate.name,
            "area_key": area.key if area else "",
            "area_name": area.name if area else "",
            "city": self.cleaned_data["city"],
            "street": self.cleaned_data["street"],
            "building": self.cleaned_data["building"],
            "landmark": self.cleaned_data.get("landmark", ""),
        }

    @property
    def installation_requested(self) -> bool:
        return bool((self.cleaned_data.get("installation") or "").strip())
