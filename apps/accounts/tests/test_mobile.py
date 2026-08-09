"""Tests for the Egyptian mobile validator (T-0402, FR-051, FR-060).

Locks apps/accounts/validators.py against the storefront reference at
static/src/js/utilities/dom.js:31-39.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.accounts.models import Address, CustomerProfile, User
from apps.accounts.validators import (
    INVALID_MOBILE_MESSAGE,
    fold_arabic_digits,
    is_valid_egyptian_mobile,
    normalize_egyptian_mobile,
    validate_egyptian_mobile,
)
from apps.shipping.models import Governorate, ServiceArea

CANONICAL = "01012345678"


# ---------------------------------------------------------------------------
# fold_arabic_digits
# ---------------------------------------------------------------------------


def test_fold_arabic_digits_maps_arabic_indic():
    assert fold_arabic_digits("٠١٢٣٤٥٦٧٨٩") == "0123456789"


def test_fold_arabic_digits_maps_extended_arabic_indic():
    assert fold_arabic_digits("۰۱۲۳۴۵۶۷۸۹") == "0123456789"


def test_fold_arabic_digits_leaves_ascii_digits_unchanged():
    assert fold_arabic_digits("01012345678") == "01012345678"


# ---------------------------------------------------------------------------
# normalize_egyptian_mobile / is_valid_egyptian_mobile — ACCEPT cases
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "01012345678",  # already canonical
        "+201012345678",  # +20 prefix
        "201012345678",  # bare 20 prefix, 12 digits
        "٠١٠١٢٣٤٥٦٧٨",  # Arabic-Indic digits
        "۰۱۰۱۲۳۴۵۶۷۸",  # Extended Arabic-Indic digits
        "010 1234 5678",  # spaces
        "010-1234-5678",  # dashes
        "+20 10 1234 5678",  # +20 with mixed spacing
    ],
)
def test_accepted_numbers_normalise_to_canonical(raw):
    assert normalize_egyptian_mobile(raw) == CANONICAL


@pytest.mark.parametrize(
    "raw",
    [
        "01012345678",
        "+201012345678",
        "201012345678",
        "٠١٠١٢٣٤٥٦٧٨",
        "۰۱۰۱۲۳۴۵۶۷۸",
        "010 1234 5678",
    ],
)
def test_accepted_numbers_are_valid(raw):
    assert is_valid_egyptian_mobile(raw) is True


def test_normalize_empty_returns_empty_string():
    assert normalize_egyptian_mobile("") == ""


# ---------------------------------------------------------------------------
# REJECT cases
# ---------------------------------------------------------------------------

REJECTED = [
    "01312345678",  # wrong carrier prefix 013
    "01412345678",  # wrong carrier prefix 014
    "0101234567",  # too short (<11 digits)
    "010123456789",  # too long (>11 digits)
    "",  # empty
    "abcdefghijk",  # letters
    "20101234567",  # 20 prefix but 11 digits, no fold -> wrong national prefix
    "+002010123456789",  # survives as 20-digit run, wrong prefix
    "٠١٣١٢٣٤٥٦٧٨",  # Arabic-Indic digits folding to 013 prefix
]


@pytest.mark.parametrize("raw", REJECTED)
def test_rejected_numbers_are_invalid(raw):
    assert is_valid_egyptian_mobile(raw) is False


@pytest.mark.parametrize("raw", REJECTED)
def test_validate_raises_for_rejected_numbers(raw):
    with pytest.raises(ValidationError):
        validate_egyptian_mobile(raw)


def test_validate_carries_exact_arabic_message_constant():
    with pytest.raises(ValidationError) as excinfo:
        validate_egyptian_mobile("01312345678")
    assert INVALID_MOBILE_MESSAGE in excinfo.value.messages


# ---------------------------------------------------------------------------
# Model field level
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.django_db


def _user(email="t0402@example.com"):
    return User.objects.create_user(email=email, password="Passw0rd!123")


def test_customer_profile_phone_accepts_valid_egyptian_mobile():
    profile = CustomerProfile(user=_user(), full_name="T", phone="+20 101 234 5678")
    profile.full_clean()
    profile.save()
    profile.refresh_from_db()
    assert profile.phone == CANONICAL


def test_customer_profile_phone_full_clean_rejects_invalid_mobile():
    profile = CustomerProfile(
        user=_user("t0402-bad@example.com"), full_name="T", phone="01312345678"
    )
    with pytest.raises(ValidationError) as excinfo:
        profile.full_clean()
    assert INVALID_MOBILE_MESSAGE in excinfo.value.error_dict["phone"][0].messages


def _address(customer, phone):
    gov = Governorate.objects.create(key="cairo", name="Cairo")
    area = ServiceArea.objects.create(key="cairo-nasr-city", governorate=gov, name="Nasr City")
    return Address(
        customer=customer,
        full_name="T",
        phone=phone,
        governorate=gov,
        area=area,
        city="Cairo",
        street="1 Test St",
        building="1",
    )


def test_address_phone_accepts_valid_egyptian_mobile():
    customer = CustomerProfile.objects.create(user=_user(), full_name="T")
    address = _address(customer, "٠١٠١٢٣٤٥٦٧٨")
    address.full_clean()
    address.save()
    address.refresh_from_db()
    assert address.phone == CANONICAL


def test_address_phone_full_clean_rejects_invalid_mobile():
    customer = CustomerProfile.objects.create(user=_user(), full_name="T")
    address = _address(customer, "0101234567")
    with pytest.raises(ValidationError) as excinfo:
        address.full_clean()
    assert INVALID_MOBILE_MESSAGE in excinfo.value.error_dict["phone"][0].messages
