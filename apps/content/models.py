"""Staff-manageable storefront content (FR-096 – FR-099).

Only content with a real business reason to change becomes database-driven.
Layout and component boundaries stay fixed (FR-099).
"""

from __future__ import annotations

from django.core.validators import MinLengthValidator
from django.db import models

from apps.core.uploads import validate_document_upload, validate_image_upload
from apps.core.models import TimeStampedModel

#: The storefront already enforces this at static/src/js/pages/contact.js:3
#: (`const MIN_MESSAGE_LENGTH = 20;`). The server must agree.
MIN_CONTACT_MESSAGE_LENGTH = 20


class NavigationGroup(models.TextChoices):
    PRIMARY = "primary", "التنقل الرئيسي"
    UTILITY = "utility", "أدوات"
    FOOTER = "footer", "التذييل"


class HomeSection(TimeStampedModel):
    key = models.SlugField("المفتاح", max_length=60, unique=True)
    heading = models.CharField("العنوان", max_length=160, blank=True, default="")
    eyebrow = models.CharField("عنوان فرعي", max_length=120, blank=True, default="")
    body = models.TextField("النص", blank=True, default="")
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّل", default=True)
    #: Structured presentation copy for the section (hero blocks, trust strips,
    #: metric lists, use-case cards…). The storefront renders this instead of
    #: reading a JSON fixture at request time (FR-096, FR-099, T-1608), which is
    #: what makes the page copy staff-editable. Layout and component boundaries
    #: are NOT stored here — only the words and the local asset paths.
    data = models.JSONField("المحتوى المنسّق", default=dict, blank=True)

    class Meta:
        verbose_name = "قسم الصفحة الرئيسية"
        verbose_name_plural = "أقسام الصفحة الرئيسية"
        ordering = ["position", "key"]

    def __str__(self) -> str:
        return self.heading or self.key


class Banner(TimeStampedModel):
    title = models.CharField("العنوان", max_length=160)
    image = models.ImageField(
        "الصورة", upload_to="banners/", blank=True, null=True,
        validators=[validate_image_upload],
    )
    legacy_image_path = models.CharField(max_length=255, blank=True, default="")
    link = models.CharField("الرابط", max_length=255, blank=True, default="")
    starts_at = models.DateTimeField("يبدأ في", null=True, blank=True)
    ends_at = models.DateTimeField("ينتهي في", null=True, blank=True)
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "بانر"
        verbose_name_plural = "البانرات"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.title


class Partner(TimeStampedModel):
    name = models.CharField("الاسم", max_length=120)
    logo = models.ImageField(
        "الشعار", upload_to="partners/", blank=True, null=True,
        validators=[validate_image_upload],
    )
    legacy_image_path = models.CharField(max_length=255, blank=True, default="")
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "شريك"
        verbose_name_plural = "الشركاء"
        ordering = ["position", "name"]

    def __str__(self) -> str:
        return self.name


class FAQ(TimeStampedModel):
    legacy_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    question = models.CharField("السؤال", max_length=255)
    answer = models.TextField("الإجابة")
    page = models.CharField("الصفحة", max_length=40, blank=True, default="")
    products = models.ManyToManyField(
        "catalog.Product", blank=True, related_name="faqs", verbose_name="المنتجات"
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "سؤال شائع"
        verbose_name_plural = "الأسئلة الشائعة"
        ordering = ["position", "id"]

    def __str__(self) -> str:
        return self.question


class StaticPage(TimeStampedModel):
    slug = models.SlugField("المعرف", max_length=80, unique=True)
    title = models.CharField("العنوان", max_length=160)
    body = models.TextField("المحتوى", blank=True, default="")
    seo_title = models.CharField("عنوان SEO", max_length=160, blank=True, default="")
    seo_description = models.CharField("وصف SEO", max_length=255, blank=True, default="")
    is_published = models.BooleanField("منشورة", default=True)

    class Meta:
        verbose_name = "صفحة ثابتة"
        verbose_name_plural = "الصفحات الثابتة"
        ordering = ["slug"]

    def __str__(self) -> str:
        return self.title


class NavigationItem(TimeStampedModel):
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="العنصر الأعلى",
    )
    label = models.CharField("النص", max_length=120)
    href = models.CharField("الرابط", max_length=255, blank=True, default="")
    route_name = models.CharField(
        "اسم المسار",
        max_length=80,
        blank=True,
        default="",
        help_text="اسم مسار Django مفضّل على الرابط الثابت.",
    )
    icon = models.CharField("الأيقونة", max_length=60, blank=True, default="")
    group = models.CharField(
        "المجموعة",
        max_length=16,
        choices=NavigationGroup.choices,
        default=NavigationGroup.PRIMARY,
    )
    position = models.PositiveSmallIntegerField("الترتيب", default=0)
    is_active = models.BooleanField("مفعّل", default=True)

    class Meta:
        verbose_name = "عنصر تنقل"
        verbose_name_plural = "عناصر التنقل"
        ordering = ["group", "position", "id"]

    def __str__(self) -> str:
        return self.label


class NewsletterSubscription(TimeStampedModel):
    email = models.EmailField("البريد الإلكتروني", unique=True)
    source = models.CharField("المصدر", max_length=60, blank=True, default="")
    confirmed = models.BooleanField("مؤكد", default=False)
    ip_hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "اشتراك النشرة"
        verbose_name_plural = "اشتراكات النشرة"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class ContactMessageStatus(models.TextChoices):
    NEW = "new", "جديدة"
    IN_PROGRESS = "in_progress", "قيد المعالجة"
    RESOLVED = "resolved", "تم الرد"
    SPAM = "spam", "غير مرغوبة"


class ContactMessage(TimeStampedModel):
    name = models.CharField("الاسم", max_length=120)
    email = models.EmailField("البريد الإلكتروني")
    phone = models.CharField("رقم الموبايل", max_length=16, blank=True, default="")
    subject = models.CharField("الموضوع", max_length=120)
    message = models.TextField(
        "الرسالة", validators=[MinLengthValidator(MIN_CONTACT_MESSAGE_LENGTH)]
    )
    status = models.CharField(
        "الحالة",
        max_length=16,
        choices=ContactMessageStatus.choices,
        default=ContactMessageStatus.NEW,
    )
    ip_hash = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = "رسالة تواصل"
        verbose_name_plural = "رسائل التواصل"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.subject} — {self.name}"
