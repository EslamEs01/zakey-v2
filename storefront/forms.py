"""Storefront input forms (T-1604, FR-039, threat T-03).

Every field here is an identifier or a quantity. There is deliberately no price,
discount, VAT, shipping or total field anywhere in this module: those are
computed from database rows in the service layer, so a tampered request body has
nothing to tamper with.
"""

from __future__ import annotations

from django import forms
from django.db import transaction

from apps.accounts.validators import normalize_egyptian_mobile, validate_egyptian_mobile
from apps.catalog.models import Product, ProductVariant
from apps.core.models import PublicationStatus, SiteSetting
from apps.content.models import MIN_CONTACT_MESSAGE_LENGTH
from apps.shipping.models import Governorate, ServiceArea

#: Same wording the checkout uses, so one rule reads the same everywhere.
INVALID_NAME = "اكتب الاسم بالكامل بالعربية."


class VariantField(forms.IntegerField):
    """A variant id resolved to a purchasable variant, or a field error."""

    def clean(self, value):
        pk = super().clean(value)
        variant = (
            ProductVariant.objects.filter(pk=pk, is_active=True)
            .select_related("product", "stock_item")
            .first()
        )
        if variant is None or variant.product.status != PublicationStatus.PUBLISHED:
            raise forms.ValidationError("هذا المنتج غير متاح حاليًا.")
        return variant


class AddToCartForm(forms.Form):
    variant = VariantField()
    quantity = forms.IntegerField(min_value=1, required=False)

    def clean_quantity(self):
        quantity = self.cleaned_data.get("quantity") or 1
        # The server owns the bound, not the number input's max attribute.
        return min(quantity, SiteSetting.objects.get_solo().max_line_quantity)


class UpdateCartLineForm(forms.Form):
    """Quantity 0 is legal and means "remove this line"."""

    variant = VariantField()
    quantity = forms.IntegerField(min_value=0)

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        return min(quantity, SiteSetting.objects.get_solo().max_line_quantity)


class RemoveCartLineForm(forms.Form):
    variant = VariantField()


class CouponForm(forms.Form):
    coupon = forms.CharField(max_length=24, required=False)

    def clean_coupon(self):
        return (self.cleaned_data.get("coupon") or "").strip().upper()


class WishlistToggleForm(forms.Form):
    product = forms.IntegerField()

    def clean_product(self):
        product = Product.objects.filter(
            pk=self.cleaned_data["product"], status=PublicationStatus.PUBLISHED
        ).first()
        if product is None:
            raise forms.ValidationError("هذا المنتج غير متاح حاليًا.")
        return product


class HoneypotMixin(forms.Form):
    """A field only an automated submitter fills in (threat T-14).

    Cheap, invisible to real users and to screen readers, and it costs a bot
    nothing to defeat — so it is a filter, not the rate limit itself.
    """

    company = forms.CharField(required=False)

    def clean_company(self):
        if self.cleaned_data.get("company"):
            raise forms.ValidationError("تعذّر إرسال النموذج.")
        return ""


class NewsletterForm(HoneypotMixin):
    """Newsletter sign-up (T-1206, FR-098).

    The prototype's version validated the address in the browser and then told
    the visitor, truthfully, that nothing had been saved. This one persists.
    """

    email = forms.EmailField(
        error_messages={
            "required": "اكتب بريداً إلكترونياً صحيحاً، مثل name@example.com",
            "invalid": "اكتب بريداً إلكترونياً صحيحاً، مثل name@example.com",
        }
    )

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class AddressForm(forms.Form):
    """A saved delivery address (T-1606, FR-055, INV-014)."""

    label = forms.CharField(max_length=60, required=False)
    full_name = forms.CharField(max_length=120, error_messages={"required": INVALID_NAME})
    phone = forms.CharField(max_length=18)
    governorate = forms.CharField()
    area = forms.CharField(required=False)
    city = forms.CharField(max_length=80)
    street = forms.CharField(max_length=140)
    building = forms.CharField(max_length=24)
    landmark = forms.CharField(max_length=100, required=False)
    is_default = forms.BooleanField(required=False)

    def clean_phone(self):
        value = self.cleaned_data["phone"]
        validate_egyptian_mobile(value)
        return normalize_egyptian_mobile(value)

    def clean_governorate(self):
        governorate = Governorate.objects.filter(
            key=self.cleaned_data["governorate"], is_active=True
        ).first()
        if governorate is None:
            raise forms.ValidationError("اختر المحافظة.")
        return governorate

    def clean(self):
        cleaned = super().clean()
        governorate = cleaned.get("governorate")
        key = (cleaned.get("area") or "").strip()
        cleaned["area"] = (
            ServiceArea.objects.filter(
                key=key, governorate=governorate, is_active=True
            ).first()
            if key and governorate is not None
            else None
        )
        return cleaned

    def save(self, profile):
        from apps.accounts.models import Address

        data = self.cleaned_data
        make_default = data.get("is_default") or not profile.addresses.exists()
        with transaction.atomic():
            if make_default:
                # Exactly one default per customer is a database constraint
                # (INV-014), so the old default must be cleared in the same
                # transaction rather than left to collide.
                profile.addresses.filter(is_default=True).update(is_default=False)
            return Address.objects.create(
                customer=profile,
                label=data.get("label", ""),
                full_name=data["full_name"],
                phone=data["phone"],
                governorate=data["governorate"],
                area=data.get("area"),
                city=data["city"],
                street=data["street"],
                building=data["building"],
                landmark=data.get("landmark", ""),
                is_default=make_default,
            )


class ProfileForm(forms.Form):
    """Name and mobile only.

    Deliberately narrow: email changes need a confirmation round trip, and
    ``is_staff``/``is_superuser`` must never be reachable from a storefront
    submission (FR-057).
    """

    full_name = forms.CharField(max_length=120, error_messages={"required": INVALID_NAME})
    phone = forms.CharField(max_length=18)

    def clean_phone(self):
        value = self.cleaned_data["phone"]
        validate_egyptian_mobile(value)
        return normalize_egyptian_mobile(value)


class ContactForm(HoneypotMixin):
    """Contact message (T-1206, FR-098).

    The 20-character minimum is the storefront's own rule
    (``contact.js:3 MIN_MESSAGE_LENGTH``), enforced here so the server and the
    browser agree on what counts as a message.
    """

    name = forms.CharField(max_length=120, error_messages={"required": INVALID_NAME})
    email = forms.EmailField(
        error_messages={
            "required": "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com.",
            "invalid": "اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com.",
        }
    )
    phone = forms.CharField(max_length=18, required=False)
    subject = forms.CharField(max_length=120, error_messages={"required": "اختر موضوعًا."})
    message = forms.CharField(
        min_length=MIN_CONTACT_MESSAGE_LENGTH,
        error_messages={
            "required": "اكتب رسالتك.",
            "min_length": f"اكتب {MIN_CONTACT_MESSAGE_LENGTH} حرفًا على الأقل.",
        },
    )

    def clean_phone(self):
        value = (self.cleaned_data.get("phone") or "").strip()
        if not value:
            return ""
        validate_egyptian_mobile(value)
        return normalize_egyptian_mobile(value)
