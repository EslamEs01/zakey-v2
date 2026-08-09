"""The customer address book at model and database level (T-0403, INV-014).

``tests/integration/test_account_flow.py`` drives the same behaviour over HTTP.
This file goes one layer down deliberately: "exactly one default" is a claim
about *rows*, and a claim about rows has to survive code that never passes
through the storefront form — an import, a data migration, a shell session.
So the default rule is asserted against the database constraint itself, and the
address shape is asserted against the model's own validation.
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import Address

pytestmark = pytest.mark.django_db


def _address(customer, governorate, area, **overrides) -> Address:
    fields = {
        "customer": customer,
        "full_name": "ندى إبراهيم",
        "phone": "01012345678",
        "governorate": governorate,
        "area": area,
        "city": "القاهرة",
        "street": "١٢ شارع التحرير",
        "building": "٥",
    }
    fields.update(overrides)
    return Address(**fields)


# ---------------------------------------------------------------------------
# Many addresses, exactly one default
# ---------------------------------------------------------------------------


class TestTheAddressBook:
    def test_a_customer_may_hold_several_addresses(self, customer, governorate, area):
        """FR-055: the address book is a list, not a single shipping address."""
        for index, city in enumerate(("القاهرة", "الجيزة", "الإسكندرية")):
            _address(customer, governorate, area, city=city, is_default=index == 0).save()

        assert customer.addresses.count() == 3
        assert customer.addresses.filter(is_default=True).count() == 1

    def test_the_database_refuses_a_second_default_address(self, customer, governorate, area):
        """FR-055: "exactly one default" is a partial unique index, not a convention.

        Asserted with no form and no service in the way: a second default
        inserted directly must be rejected by PostgreSQL, because that is the
        only guarantee that holds for every writer.
        """
        _address(customer, governorate, area, is_default=True).save()

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                _address(
                    customer, governorate, area, city="الجيزة", is_default=True
                ).save()

        assert customer.addresses.filter(is_default=True).count() == 1

    def test_each_customer_keeps_their_own_default(
        self, customer, other_customer, governorate, area
    ):
        """FR-055 scopes the default to the customer, not to the table."""
        _address(customer, governorate, area, is_default=True).save()
        _address(other_customer, governorate, area, is_default=True).save()

        assert Address.objects.filter(is_default=True).count() == 2

    def test_a_customer_may_keep_no_default_at_all_while_editing(
        self, customer, governorate, area
    ):
        """The constraint bounds the default above, never below.

        Clearing every default is what the storefront does one statement before
        promoting a new one; a constraint that forbade it would make swapping
        the default impossible.
        """
        _address(customer, governorate, area, is_default=True).save()
        customer.addresses.update(is_default=False)

        assert customer.addresses.filter(is_default=True).count() == 0


# ---------------------------------------------------------------------------
# The shape of one address
# ---------------------------------------------------------------------------


class TestTheAddressShape:
    def test_an_address_carries_every_field_the_courier_needs(
        self, customer, governorate, area
    ):
        """FR-055: governorate, area, city, street, building and landmark persist."""
        _address(customer, governorate, area, landmark="أمام مسجد النور").save()

        stored = Address.objects.get(customer=customer)
        assert stored.governorate_id == governorate.pk
        assert stored.area_id == area.pk
        assert stored.city == "القاهرة"
        assert stored.street == "١٢ شارع التحرير"
        assert stored.building == "٥"
        assert stored.landmark == "أمام مسجد النور"

    def test_the_landmark_may_be_left_out(self, customer, governorate, area):
        """FR-055 marks the landmark optional, and the model agrees."""
        address = _address(customer, governorate, area)
        address.full_clean()  # no landmark supplied
        address.save()

        assert Address.objects.get(pk=address.pk).landmark == ""

    @pytest.mark.parametrize("field", ["governorate", "city", "street", "building"])
    def test_the_other_location_fields_are_mandatory(
        self, customer, governorate, area, field
    ):
        """Everything FR-055 lists except the landmark must actually be given."""
        address = _address(customer, governorate, area)
        setattr(address, field, None if field == "governorate" else "")

        with pytest.raises(ValidationError) as excinfo:
            address.full_clean()
        assert field in excinfo.value.error_dict
