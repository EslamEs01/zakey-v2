"""Upload validation (T-1702, threat T-08).

An upload field is the one place a staff account can hand the server a file of
its choosing. Every guard here exists because a specific attack works without
it:

* **Extension checks are not validation.** ``payload.php`` renamed to
  ``photo.jpg`` passes any name-based check, so the file's own leading bytes are
  what decide its type.
* **SVG is rejected outright.** It is an image format that is also a document
  format: it can carry ``<script>`` and be served same-origin. There is no safe
  way to accept an SVG as a user upload here, and nothing in the design needs
  one.
* **A decompression bomb is small on disk.** A few kilobytes of PNG can decode
  to billions of pixels and take the process out of memory, so the pixel count
  is capped before the image is ever fully decoded.
* **A valid image can still carry a payload.** Polyglot files are valid JPEGs
  *and* valid archives or scripts. Re-encoding through Pillow discards
  everything that is not pixels, which is the only reliable way to strip it.
"""

from __future__ import annotations

import io

from django.core.exceptions import ValidationError

#: 5 MB. Generous for a product photo, far below anything that hurts.
MAX_IMAGE_BYTES = 5 * 1024 * 1024

#: 10 MB for a manual or spec sheet.
MAX_DOCUMENT_BYTES = 10 * 1024 * 1024

#: Decoded pixels. A 4000×4000 photo is 16M; 40M leaves headroom without
#: letting a bomb through.
MAX_IMAGE_PIXELS = 40_000_000

#: Leading bytes → format. Checked against the file itself, never its name.
_IMAGE_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\xff\xd8\xff", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
    (b"GIF87a", "GIF"),
    (b"GIF89a", "GIF"),
    (b"RIFF", "WEBP"),  # confirmed below by the WEBP tag at offset 8
)

_PDF_SIGNATURE = b"%PDF-"

#: Markers that mean "this is a document pretending to be an image".
_SVG_MARKERS = (b"<svg", b"<?xml", b"<!doctype svg")


def _read_head(uploaded, size: int = 512) -> bytes:
    position = uploaded.tell() if hasattr(uploaded, "tell") else 0
    uploaded.seek(0)
    head = uploaded.read(size)
    uploaded.seek(position)
    return head


def _reject(message: str) -> None:
    raise ValidationError(message)


def validate_image_upload(uploaded) -> None:
    """Reject anything that is not a plain, sane raster image (T-08)."""
    if uploaded is None:
        return

    size = getattr(uploaded, "size", None)
    if size is not None and size > MAX_IMAGE_BYTES:
        _reject(
            f"حجم الصورة يتجاوز الحد المسموح ({MAX_IMAGE_BYTES // (1024 * 1024)} ميجابايت)."
        )

    head = _read_head(uploaded)
    if not head:
        _reject("الملف فارغ.")

    lowered = head.lstrip()[:64].lower()
    if any(marker in lowered for marker in _SVG_MARKERS):
        _reject("صيغة SVG غير مسموح بها؛ استخدم PNG أو JPEG أو WebP.")

    detected = None
    for signature, label in _IMAGE_SIGNATURES:
        if head.startswith(signature):
            if label == "WEBP" and head[8:12] != b"WEBP":
                continue
            detected = label
            break

    if detected is None:
        _reject("صيغة الصورة غير مدعومة؛ يُقبل PNG وJPEG وWebP وGIF فقط.")

    _verify_decodable(uploaded)


def _verify_decodable(uploaded) -> None:
    """Confirm Pillow can decode it, and that it is not a decompression bomb."""
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Pillow ships with the project
        return

    position = uploaded.tell() if hasattr(uploaded, "tell") else 0
    uploaded.seek(0)
    payload = uploaded.read()
    uploaded.seek(position)

    previous_limit = Image.MAX_IMAGE_PIXELS
    Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
    try:
        with Image.open(io.BytesIO(payload)) as image:
            width, height = image.size
            if width * height > MAX_IMAGE_PIXELS:
                _reject("أبعاد الصورة كبيرة بشكل غير معقول.")
            # verify() walks the file and raises on a malformed or hostile one.
            image.verify()
    except ValidationError:
        raise
    except Image.DecompressionBombError:
        _reject("أبعاد الصورة كبيرة بشكل غير معقول.")
    except Exception:
        _reject("تعذّر قراءة الصورة؛ الملف تالف أو ليس صورة.")
    finally:
        Image.MAX_IMAGE_PIXELS = previous_limit


def reencode_image(uploaded):
    """Return a re-encoded copy carrying pixels and nothing else.

    A valid JPEG can also be a valid ZIP, or carry a script in a comment
    segment. Decoding to pixels and writing a fresh file is what discards all of
    it — there is no reliable way to *scan* for every such payload.
    """
    from django.core.files.uploadedfile import InMemoryUploadedFile
    from PIL import Image

    uploaded.seek(0)
    with Image.open(uploaded) as image:
        fmt = "PNG" if image.mode in ("RGBA", "LA", "P") else "JPEG"
        converted = image.convert("RGBA" if fmt == "PNG" else "RGB")
        buffer = io.BytesIO()
        converted.save(buffer, format=fmt, optimize=True)

    buffer.seek(0)
    name = getattr(uploaded, "name", "upload")
    stem = name.rsplit(".", 1)[0]
    extension = "png" if fmt == "PNG" else "jpg"
    return InMemoryUploadedFile(
        buffer,
        field_name=getattr(uploaded, "field_name", None),
        name=f"{stem}.{extension}",
        content_type=f"image/{extension}",
        size=buffer.getbuffer().nbytes,
        charset=None,
    )


def validate_document_upload(uploaded) -> None:
    """Only real PDFs. A manual has no reason to be anything else (T-08)."""
    if uploaded is None:
        return

    size = getattr(uploaded, "size", None)
    if size is not None and size > MAX_DOCUMENT_BYTES:
        _reject(
            f"حجم الملف يتجاوز الحد المسموح "
            f"({MAX_DOCUMENT_BYTES // (1024 * 1024)} ميجابايت)."
        )

    head = _read_head(uploaded)
    if not head.startswith(_PDF_SIGNATURE):
        _reject("صيغة الملف غير مدعومة؛ يُقبل PDF فقط.")
