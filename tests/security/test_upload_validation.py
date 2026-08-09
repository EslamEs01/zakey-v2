"""Upload validation (T-1702, threat T-08).

One test per attack, because "we validate uploads" is not a claim that can be
checked — "a PHP script renamed to .jpg is rejected" is.

Every payload below is constructed in memory. Nothing here writes to the media
root or executes anything.
"""

from __future__ import annotations

import io

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.uploads import (
    MAX_IMAGE_BYTES,
    MAX_IMAGE_PIXELS,
    validate_document_upload,
    validate_image_upload,
)


def png_bytes(width: int = 4, height: int = 4) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "red").save(buffer, format="PNG")
    return buffer.getvalue()


def jpeg_bytes(width: int = 4, height: int = 4) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (width, height), "blue").save(buffer, format="JPEG")
    return buffer.getvalue()


def upload(name: str, payload: bytes, content_type: str = "image/png"):
    return SimpleUploadedFile(name, payload, content_type=content_type)


# ---------------------------------------------------------------------------
# The happy path must keep working
# ---------------------------------------------------------------------------


class TestLegitimateUploads:
    def test_a_real_png_is_accepted(self):
        validate_image_upload(upload("photo.png", png_bytes()))

    def test_a_real_jpeg_is_accepted(self):
        validate_image_upload(upload("photo.jpg", jpeg_bytes(), "image/jpeg"))

    def test_a_real_pdf_is_accepted(self):
        validate_document_upload(
            upload("manual.pdf", b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\ntrailer\n", "application/pdf")
        )


# ---------------------------------------------------------------------------
# One test per attack
# ---------------------------------------------------------------------------


class TestAttacks:
    def test_a_php_script_renamed_to_jpg_is_rejected(self):
        """Attack: extension spoofing. The name says jpg; the bytes say PHP."""
        payload = b"<?php system($_GET['c']); ?>"

        with pytest.raises(ValidationError):
            validate_image_upload(upload("photo.jpg", payload, "image/jpeg"))

    def test_an_html_file_renamed_to_png_is_rejected(self):
        """Attack: stored XSS via a same-origin 'image'."""
        payload = b"<html><script>alert(1)</script></html>"

        with pytest.raises(ValidationError):
            validate_image_upload(upload("photo.png", payload))

    def test_an_svg_is_rejected(self):
        """Attack: SVG is a document format. It can carry script."""
        payload = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'

        with pytest.raises(ValidationError) as caught:
            validate_image_upload(upload("logo.svg", payload, "image/svg+xml"))

        assert "SVG" in str(caught.value)

    def test_an_svg_renamed_to_png_is_still_rejected(self):
        """The rejection must be by content, not by extension."""
        payload = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'

        with pytest.raises(ValidationError):
            validate_image_upload(upload("logo.png", payload))

    def test_an_oversized_file_is_rejected(self):
        """Attack: disk exhaustion."""
        payload = png_bytes() + b"\x00" * (MAX_IMAGE_BYTES + 1)

        with pytest.raises(ValidationError) as caught:
            validate_image_upload(upload("huge.png", payload))

        assert "الحد المسموح" in str(caught.value)

    def test_a_decompression_bomb_is_rejected(self):
        """Attack: a few KB on disk that decodes to billions of pixels."""
        from PIL import Image

        side = 12000  # 144M pixels, well past the cap
        buffer = io.BytesIO()
        previous = Image.MAX_IMAGE_PIXELS
        Image.MAX_IMAGE_PIXELS = None
        try:
            Image.new("L", (side, side), 0).save(buffer, format="PNG", optimize=True)
        finally:
            Image.MAX_IMAGE_PIXELS = previous

        payload = buffer.getvalue()
        assert len(payload) < MAX_IMAGE_BYTES, "precondition: small on disk"

        with pytest.raises(ValidationError):
            validate_image_upload(upload("bomb.png", payload))

    def test_a_truncated_image_is_rejected(self):
        """Attack: a malformed file that crashes the decoder downstream."""
        payload = png_bytes(64, 64)[:40]

        with pytest.raises(ValidationError):
            validate_image_upload(upload("broken.png", payload))

    def test_an_empty_file_is_rejected(self):
        with pytest.raises(ValidationError):
            validate_image_upload(upload("empty.png", b""))

    def test_a_zip_renamed_to_png_is_rejected(self):
        payload = b"PK\x03\x04" + b"\x00" * 64

        with pytest.raises(ValidationError):
            validate_image_upload(upload("archive.png", payload))

    def test_a_fake_webp_header_is_rejected(self):
        """RIFF alone is not WebP; the format tag at offset 8 must match too."""
        payload = b"RIFF" + b"\x00\x00\x00\x00" + b"AVI " + b"\x00" * 32

        with pytest.raises(ValidationError):
            validate_image_upload(upload("clip.webp", payload, "image/webp"))

    def test_an_executable_renamed_to_pdf_is_rejected(self):
        payload = b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 32

        with pytest.raises(ValidationError):
            validate_document_upload(upload("manual.pdf", payload, "application/pdf"))

    def test_an_image_is_not_accepted_as_a_document(self):
        with pytest.raises(ValidationError):
            validate_document_upload(upload("manual.pdf", png_bytes(), "application/pdf"))


# ---------------------------------------------------------------------------
# Re-encoding strips whatever survived the checks
# ---------------------------------------------------------------------------


class TestReencoding:
    def test_a_trailing_payload_does_not_survive(self):
        """Polyglot: a valid PNG with an archive appended after IEND."""
        from apps.core.uploads import reencode_image

        payload = png_bytes(16, 16) + b"PK\x03\x04HIDDEN-PAYLOAD"
        cleaned = reencode_image(upload("polyglot.png", payload))

        cleaned.seek(0)
        assert b"HIDDEN-PAYLOAD" not in cleaned.read()

    def test_the_image_still_decodes_after_re_encoding(self):
        from PIL import Image

        from apps.core.uploads import reencode_image

        cleaned = reencode_image(upload("photo.png", png_bytes(20, 10)))

        cleaned.seek(0)
        with Image.open(cleaned) as image:
            assert image.size == (20, 10)

    def test_exif_metadata_does_not_survive(self):
        """Location data in a product photo is a privacy leak (NFR-012).

        Built with Pillow alone so the test carries no extra dependency: a JPEG
        is written with an EXIF block, then re-encoded, then checked.
        """
        from PIL import Image

        from apps.core.uploads import reencode_image

        buffer = io.BytesIO()
        exif = Image.Exif()
        exif[0x010E] = "SECRET-LOCATION-TAG"  # ImageDescription
        Image.new("RGB", (8, 8), "green").save(buffer, format="JPEG", exif=exif)
        original = buffer.getvalue()
        assert b"SECRET-LOCATION-TAG" in original, "precondition: EXIF is present"

        cleaned = reencode_image(upload("photo.jpg", original, "image/jpeg"))

        cleaned.seek(0)
        assert b"SECRET-LOCATION-TAG" not in cleaned.read()


# ---------------------------------------------------------------------------
# The validators are actually wired to the fields
# ---------------------------------------------------------------------------


class TestValidatorsAreInstalled:
    @pytest.mark.parametrize(
        "model_path,field_name,validator",
        [
            ("apps.catalog.models.Category", "image", validate_image_upload),
            ("apps.catalog.models.Brand", "logo", validate_image_upload),
            ("apps.catalog.models.ProductImage", "image", validate_image_upload),
            ("apps.catalog.models.ProductDocument", "file", validate_document_upload),
            ("apps.content.models.Banner", "image", validate_image_upload),
            ("apps.content.models.Partner", "logo", validate_image_upload),
        ],
    )
    def test_every_upload_field_validates(self, model_path, field_name, validator):
        from django.utils.module_loading import import_string

        model = import_string(model_path)
        field = model._meta.get_field(field_name)

        assert validator in field.validators, (
            f"{model_path}.{field_name} accepts unvalidated uploads"
        )

    def test_no_upload_field_escapes_validation(self):
        """Guard the guard: a new upload field must not slip through."""
        from django.apps import apps as django_apps
        from django.db.models import FileField

        from apps.core.uploads import validate_document_upload, validate_image_upload

        unguarded = []
        for model in django_apps.get_models():
            if not model._meta.app_label.startswith(("catalog", "content", "core")):
                continue
            for field in model._meta.get_fields():
                if isinstance(field, FileField):
                    if not any(
                        v in field.validators
                        for v in (validate_image_upload, validate_document_upload)
                    ):
                        unguarded.append(f"{model._meta.label}.{field.name}")

        assert unguarded == [], f"upload fields with no validation: {unguarded}"


@pytest.mark.django_db
class TestUploadValidationOverHttp:
    def test_the_admin_refuses_a_disguised_upload(self, client, db, product):
        """End to end: the guard must hold at the HTTP boundary too."""
        from apps.accounts.models import User

        staff = User.objects.create_superuser(
            email="upload@zakey.test", password="Admin!2345"
        )
        client.force_login(staff)

        from apps.catalog.models import ProductImage

        before = ProductImage.objects.count()
        client.post(
            "/admin/catalog/productimage/add/",
            {
                "product": str(product.pk),
                "image": upload("evil.png", b"<?php echo 1; ?>"),
                "alt": "صورة",
                "position": "0",
            },
        )

        assert ProductImage.objects.count() == before
