"""Bulk image upload for a product (FR-104).

Adding a gallery one inline row at a time is the single slowest thing in the
catalogue admin: a product carries several photos, and each one costs a click on
"add another", a file picker, and an alt text. This adds one form that takes a
whole selection at once.

The uploads go through exactly the same validation as the inline — the model
field's own ``validate_image_upload`` — so this is a faster path to the same
guarantees, never a way around them (T-1702).
"""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import path, reverse

from apps.core.uploads import validate_image_upload

from .models import Product, ProductImage


class MultipleFileInput(forms.ClearableFileInput):
    """Django ships no multi-file widget; ``allow_multiple_selected`` enables it."""

    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    """A file field that cleans *every* selected file, not just the last one.

    ``FileField.clean`` is written for one file. Given a multi-file input it
    silently validates the last and drops the rest, so this has to fan out
    explicitly or a bad file in position one would be accepted unchecked.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single = super().clean
        if isinstance(data, (list, tuple)):
            return [single(item, initial) for item in data]
        return [single(data, initial)]


class BulkImageUploadForm(forms.Form):
    images = MultipleImageField(
        label="الصور",
        help_text="يمكن اختيار عدة ملفات معًا (PNG أو JPEG أو WebP، حتى ٥ ميجابايت للصورة).",
    )
    alt = forms.CharField(
        label="النص البديل",
        max_length=200,
        required=False,
        help_text="يُطبَّق على كل الصور؛ يُترك فارغًا لاستخدام اسم المنتج.",
    )
    alt_en = forms.CharField(
        label="النص البديل (إنجليزي)", max_length=200, required=False
    )

    def clean_images(self):
        files = self.cleaned_data["images"]
        errors = []
        for uploaded in files:
            try:
                validate_image_upload(uploaded)
            except ValidationError as error:
                errors.append(f"{uploaded.name}: {error.messages[0]}")
        if errors:
            # Every rejected file is named. Reporting only the first would mean
            # a staff member fixes one, re-uploads, and is refused again.
            raise ValidationError(errors)
        return files


def bulk_upload_view(model_admin, request, object_id):
    product = get_object_or_404(Product, pk=object_id)

    if not model_admin.has_change_permission(request, product):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

    if request.method == "POST":
        form = BulkImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            # Continue the existing gallery rather than restarting at zero, so
            # a second batch lands after the first instead of interleaving.
            start = (
                ProductImage.objects.filter(product=product)
                .order_by("-position")
                .values_list("position", flat=True)
                .first()
                or 0
            )
            created = [
                ProductImage(
                    product=product,
                    image=uploaded,
                    alt=form.cleaned_data["alt"] or product.name,
                    alt_en=form.cleaned_data["alt_en"] or product.name_en,
                    position=start + offset,
                )
                for offset, uploaded in enumerate(form.cleaned_data["images"], start=1)
            ]
            ProductImage.objects.bulk_create(created)
            model_admin.message_user(
                request, f"تمت إضافة {len(created)} صورة.", messages.SUCCESS
            )
            return HttpResponseRedirect(
                reverse("admin:catalog_product_change", args=[product.pk])
            )
    else:
        form = BulkImageUploadForm()

    context = {
        **model_admin.admin_site.each_context(request),
        "opts": Product._meta,
        "original": product,
        "product": product,
        "form": form,
        "title": f"رفع صور متعددة — {product.name}",
        "existing_count": product.images.count(),
    }
    return render(request, "admin/catalog/bulk_image_upload.html", context)


def bulk_upload_urls(model_admin) -> list:
    return [
        path(
            "<path:object_id>/bulk-images/",
            model_admin.admin_site.admin_view(
                lambda request, object_id: bulk_upload_view(
                    model_admin, request, object_id
                )
            ),
            name="catalog_product_bulk_images",
        )
    ]
