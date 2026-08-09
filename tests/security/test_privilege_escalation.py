"""Privilege-escalation sweep (T-0407, FR-057).

Assert that ``is_staff`` / ``is_superuser`` cannot be flipped from any
storefront-reachable form surface: neither because the field exists to be
filled, nor because visited data is mass-assigned onto the user record.
"""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model

from apps.accounts import forms, services

User = get_user_model()

pytestmark = pytest.mark.django_db

ESCALATION_KEYS = ("is_staff", "is_superuser")

REGISTRATION_DATA = {
    "email": "mallory@example.com",
    "full_name": "مايلوري الشرير",
    "mobile": "01012345678",
    "password": "Zakey-Pass!123",
    "password_confirm": "Zakey-Pass!123",
    "is_staff": "1",
    "is_superuser": "on",
    "email_verified": "1",  # adjacent privilege: verification must not flip either
    "groups": ["1"],
    "user_permissions": ["1"],
}


# ---------------------------------------------------------------------------
# The forms must not even declare the fields
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("form_cls", [forms.RegistrationForm, forms.PasswordResetRequestForm])
@pytest.mark.parametrize("field", ESCALATION_KEYS)
def test_forms_declare_no_privilege_field(form_cls, field):
    assert field not in form_cls.base_fields
    declared = {name for cls in form_cls.mro() for name in getattr(cls, "declared_fields", {})}
    assert field not in declared


def test_no_modelform_reaches_the_user_model():
    """Registration stays a plain Form: ModelForm mass-assignment is the classic
    escalation vector, so we assert none of the public forms are ModelForms
    bound to the auth user model."""
    from django.forms import ModelForm

    for form_cls in (
        forms.RegistrationForm,
        forms.LoginForm,
        forms.PasswordResetRequestForm,
        forms.SetNewPasswordForm,
    ):
        assert not (issubclass(form_cls, ModelForm) and form_cls._meta.model is User)


# ---------------------------------------------------------------------------
# Mass-assignment: extra keys in visited data are dropped, never saved
# ---------------------------------------------------------------------------


def test_registration_ignores_every_privilege_field_on_save():
    form = forms.RegistrationForm(data=REGISTRATION_DATA)
    assert form.is_valid(), form.errors.as_json()

    # Visited extras never reach cleaned_data — that is the wall.
    assert "is_staff" not in form.cleaned_data
    assert "is_superuser" not in form.cleaned_data
    assert "email_verified" not in form.cleaned_data
    assert "groups" not in form.cleaned_data
    assert "user_permissions" not in form.cleaned_data

    result = services.register(form)
    result.user.refresh_from_db()
    assert result.user.is_staff is False
    assert result.user.is_superuser is False
    assert result.profile.email_verified is False
    assert result.user.groups.count() == 0
    assert result.user.user_permissions.count() == 0


def test_login_form_cannot_be_mass_assigned_onto_a_user():
    existing = User.objects.create_user(email="grounded@example.com", password="StrongPass!234")
    form = forms.LoginForm(
        data={
            "email": "grounded@example.com",
            "password": "StrongPass!234",
            "is_staff": "1",
            "is_superuser": "1",
        },
        client_ip="198.51.100.99",
    )
    assert form.is_valid(), form.errors.as_json()
    existing.refresh_from_db()
    assert existing.is_staff is False and existing.is_superuser is False


def test_set_password_form_never_touches_privilege_fields():
    user = User.objects.create_user(email="reset@example.com", password="OldPass!1234")
    form = forms.SetNewPasswordForm(
        data={
            "password": "Fresh-Pass!456",
            "password_confirm": "Fresh-Pass!456",
            "is_staff": "1",
            "is_superuser": "1",
        },
        user=user,
    )
    assert form.is_valid(), form.errors.as_json()
    form.confirm_password_change()
    user.refresh_from_db()
    assert user.check_password("Fresh-Pass!456")
    assert user.is_staff is False and user.is_superuser is False


# ---------------------------------------------------------------------------
# The registered account's flags stay as created under every form
# ---------------------------------------------------------------------------


def test_all_forms_leave_staff_flags_isolated():
    data = dict(REGISTRATION_DATA, email="clean@example.com")
    form = forms.RegistrationForm(data=data)
    assert form.is_valid(), form.errors.as_json()
    result = services.register(form)

    staff_qs = User.objects.exclude(is_staff=False).exclude(is_superuser=False)
    assert result.user.pk not in staff_qs.values_list("pk", flat=True)
