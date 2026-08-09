"""Customers, profiles and addresses (FR-050 – FR-059, INV-010, INV-014)."""

from __future__ import annotations

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.core.models import TimeStampedModel

from .validators import normalize_egyptian_mobile, validate_egyptian_mobile


class UserManager(BaseUserManager):
    """Email is the login identifier (FR-050); there is no username."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra):
        if not email:
            raise ValueError("البريد الإلكتروني مطلوب.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_active", True)
        if extra.get("is_staff") is not True or extra.get("is_superuser") is not True:
            raise ValueError("المستخدم الخارق يجب أن يكون is_staff و is_superuser.")
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    username = None  # replaced by email
    email = models.EmailField("البريد الإلكتروني", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="customer_profile"
    )
    full_name = models.CharField("الاسم بالكامل", max_length=120)
    phone = models.CharField(
        "رقم الموبايل",
        max_length=16,
        blank=True,
        default="",
        validators=[validate_egyptian_mobile],
    )
    phone_verified = models.BooleanField("تم توثيق الرقم", default=False)
    email_verified = models.BooleanField("تم توثيق البريد", default=False)
    accepts_marketing = models.BooleanField("يقبل الرسائل التسويقية", default=False)

    class Meta:
        verbose_name = "ملف عميل"
        verbose_name_plural = "ملفات العملاء"
        constraints = [
            # Phone uniqueness applies only once verified (FR-052): unverified
            # duplicates are a data-entry reality, verified duplicates are not.
            models.UniqueConstraint(
                fields=["phone"],
                condition=models.Q(phone_verified=True) & ~models.Q(phone=""),
                name="unique_verified_customer_phone",
            )
        ]

    def __str__(self) -> str:
        return self.full_name or str(self.user_id)

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = normalize_egyptian_mobile(self.phone)
        super().save(*args, **kwargs)

    @property
    def masked_phone(self) -> str:
        """Admin default view; full value needs accounts.view_full_contact (FR-112)."""
        if not self.phone or len(self.phone) < 11:
            return self.phone
        return f"{self.phone[:3]}****{self.phone[-2:]}"


class Address(TimeStampedModel):
    customer = models.ForeignKey(
        "accounts.CustomerProfile", on_delete=models.CASCADE, related_name="addresses"
    )
    label = models.CharField("اسم العنوان", max_length=60, blank=True, default="")
    full_name = models.CharField("اسم المستلم", max_length=120)
    phone = models.CharField(
        "رقم الموبايل", max_length=16, validators=[validate_egyptian_mobile]
    )
    governorate = models.ForeignKey(
        "shipping.Governorate", on_delete=models.PROTECT, related_name="addresses"
    )
    area = models.ForeignKey(
        "shipping.ServiceArea",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="addresses",
    )
    city = models.CharField("المدينة أو المركز", max_length=80)
    street = models.CharField("الشارع والعنوان التفصيلي", max_length=140)
    building = models.CharField("رقم المبنى", max_length=24)
    landmark = models.CharField("علامة مميزة", max_length=100, blank=True, default="")
    is_default = models.BooleanField("العنوان الافتراضي", default=False)

    class Meta:
        verbose_name = "عنوان"
        verbose_name_plural = "العناوين"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            # Exactly one default per customer, enforced by the database (INV-014).
            models.UniqueConstraint(
                fields=["customer"],
                condition=models.Q(is_default=True),
                name="unique_default_address_per_customer",
            )
        ]

    def __str__(self) -> str:
        return f"{self.label or self.full_name} — {self.city}"

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = normalize_egyptian_mobile(self.phone)
        super().save(*args, **kwargs)
