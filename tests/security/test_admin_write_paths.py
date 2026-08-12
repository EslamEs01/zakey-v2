"""Every admin write path a staff member can actually reach must work.

These are regression tests for failures a permission matrix cannot catch: an
"Add" button that leads to a form which cannot be saved, an upload that is
refused for the wrong reason, an export format that silently is not offered.
Each one renders as a 500 or a dead end to the staff member using it, and none
of them is visible from reading the ModelAdmin.
"""

from __future__ import annotations

import io

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from django.urls import NoReverseMatch, reverse

pytestmark = pytest.mark.django_db

PASSWORD = "AdminWritePaths123!"

#: Fields a form may legitimately omit because it sets them another way.
ALLOWED_ABSENT = {"accounts.User": {"password"}}


@pytest.fixture
def superuser(db):
    User = get_user_model()
    user = User.objects.create_superuser(email="write-paths@zakey.local", password=PASSWORD)
    return user


@pytest.fixture
def admin_client_su(superuser):
    client = Client()
    assert client.login(email=superuser.email, password=PASSWORD)
    return client


def png_bytes(size=(32, 32)):
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(buffer, format="PNG")
    return buffer.getvalue()


class TestEveryOfferedAddFormCanBeSaved:
    """An add form that cannot produce a valid row is a 500 behind a button.

    ``payments.Refund`` was exactly that: every field was read-only, so the form
    rendered only ``reason`` and saving raised ``IntegrityError`` on the NOT
    NULL ``amount``. The guard is structural — if the admin offers "add", the
    form must contain enough editable fields to satisfy the model.
    """

    def test_no_admin_offers_an_add_form_it_cannot_save(self, superuser):
        request = RequestFactory().get("/admin/")
        request.user = superuser

        offenders = []
        for model, model_admin in admin.site._registry.items():
            if not model_admin.has_add_permission(request):
                continue
            form = model_admin.get_form(request)()
            editable = set(form.fields)
            required = {
                field.name
                for field in model._meta.get_fields()
                if getattr(field, "editable", False)
                and not getattr(field, "blank", True)
                and not getattr(field, "has_default", lambda: True)()
                and not getattr(field, "primary_key", False)
                and not getattr(field, "auto_created", False)
            }
            # Django's UserAdmin add form collects password1/password2 and
            # hashes them into `password`, so the raw field is legitimately
            # absent from the form.
            missing = required - editable - ALLOWED_ABSENT.get(model._meta.label, set())
            if missing:
                offenders.append(f"{model._meta.label}: {sorted(missing)}")

        assert not offenders, (
            "these admins offer an Add button whose form omits a required field, "
            f"so saving raises IntegrityError: {offenders}"
        )

    def test_the_refund_admin_offers_no_add_form(self, superuser):
        """Refunds go through the payment's refund action, which is the only
        path that checks the refundable balance (INV-004)."""
        request = RequestFactory().get("/admin/")
        request.user = superuser
        from apps.payments.models import Refund

        assert admin.site._registry[Refund].has_add_permission(request) is False

    def test_the_refund_add_url_is_refused(self, admin_client_su):
        response = admin_client_su.get(reverse("admin:payments_refund_add"))

        assert response.status_code == 403


class TestRefundsAreIssuedFromThePayment:
    @pytest.fixture
    def order(self, db):
        from decimal import Decimal

        from apps.orders.models import Order

        return Order.objects.create(
            number="ZK-REFUND-0001",
            email="nada@example.com",
            phone="01012345678",
            idempotency_key="refund-idem-0001",
            subtotal=Decimal("1000.00"),
            grand_total=Decimal("1000.00"),
        )

    @pytest.fixture
    def captured_payment(self, order):
        from decimal import Decimal

        from apps.payments.models import Payment, PaymentMethod, PaymentState

        # collects_on_delivery, so `gateway_for` resolves; a method with no
        # gateway is refused by design and would test the wrong thing.
        method = PaymentMethod.objects.create(
            code="payment-cod", label="الدفع عند الاستلام", collects_on_delivery=True
        )
        return Payment.objects.create(
            order=order,
            method=method,
            amount=Decimal("1000.00"),
            currency="EGP",
            state=PaymentState.CAPTURED,
        )

    def test_the_action_renders_a_form_asking_for_amount_and_reason(
        self, admin_client_su, captured_payment
    ):
        response = admin_client_su.post(
            reverse("admin:payments_payment_changelist"),
            {
                "action": "refund_payments",
                "_selected_action": [str(captured_payment.pk)],
                "index": "0",
            },
        )

        assert response.status_code == 200
        body = response.content.decode()
        assert 'name="amount"' in body
        assert 'name="reason"' in body

    def test_applying_it_records_the_refund_through_the_service(
        self, admin_client_su, captured_payment
    ):
        from decimal import Decimal

        from apps.payments.models import Refund

        response = admin_client_su.post(
            reverse("admin:payments_payment_changelist"),
            {
                "action": "refund_payments",
                "_selected_action": [str(captured_payment.pk)],
                "index": "0",
                "apply": "1",
                "amount": "250.00",
                "reason": "عيب في المنتج",
            },
            follow=True,
        )

        assert response.status_code == 200
        refund = Refund.objects.get(payment=captured_payment)
        assert refund.amount == Decimal("250.00")
        # The service moved the payment state with the refund; a hand-typed
        # Refund row would have left it CAPTURED.
        captured_payment.refresh_from_db()
        assert captured_payment.state == "partially_refunded"

    def test_an_over_refund_is_reported_not_raised(
        self, admin_client_su, captured_payment
    ):
        from apps.payments.models import Refund

        response = admin_client_su.post(
            reverse("admin:payments_payment_changelist"),
            {
                "action": "refund_payments",
                "_selected_action": [str(captured_payment.pk)],
                "index": "0",
                "apply": "1",
                "amount": "999999.00",
                "reason": "خطأ",
            },
            follow=True,
        )

        assert response.status_code == 200, "an over-refund must not 500"
        assert not Refund.objects.filter(payment=captured_payment).exists()


class TestBulkImageUpload:
    def test_it_accepts_several_files_at_once(self, admin_client_su, product):
        url = reverse("admin:catalog_product_bulk_images", args=[product.pk])
        files = [
            SimpleUploadedFile(f"shot{index}.png", png_bytes(), content_type="image/png")
            for index in range(4)
        ]

        response = admin_client_su.post(
            url, {"images": files, "alt": "صورة", "alt_en": "Photo"}, follow=True
        )

        assert response.status_code == 200
        assert product.images.count() == 4
        assert {image.alt for image in product.images.all()} == {"صورة"}
        assert {image.alt_en for image in product.images.all()} == {"Photo"}

    def test_positions_continue_after_an_existing_gallery(
        self, admin_client_su, product
    ):
        from apps.catalog.models import ProductImage

        ProductImage.objects.create(product=product, alt="أول", position=7)
        url = reverse("admin:catalog_product_bulk_images", args=[product.pk])

        admin_client_su.post(
            url,
            {"images": [SimpleUploadedFile("a.png", png_bytes(), content_type="image/png")]},
            follow=True,
        )

        assert product.images.order_by("-position").first().position == 8

    def test_one_bad_file_rejects_the_whole_batch_and_names_it(
        self, admin_client_su, product
    ):
        """Partial success would leave staff guessing which of twenty files
        failed, so the batch is refused as a unit with the filename reported."""
        url = reverse("admin:catalog_product_bulk_images", args=[product.pk])
        files = [
            SimpleUploadedFile("good.png", png_bytes(), content_type="image/png"),
            SimpleUploadedFile("payload.php.png", b"<?php echo 1; ?>", content_type="image/png"),
        ]

        response = admin_client_su.post(url, {"images": files})

        assert response.status_code == 200
        assert "payload.php.png" in response.content.decode()
        assert product.images.count() == 0

    def test_it_refuses_a_staff_member_without_change_permission(self, db, product):
        from django.contrib.auth.models import Permission

        User = get_user_model()
        viewer = User.objects.create_user(
            email="viewer@zakey.local", password=PASSWORD, is_staff=True
        )
        viewer.user_permissions.add(Permission.objects.get(codename="view_product"))
        client = Client()
        assert client.login(email=viewer.email, password=PASSWORD)

        response = client.get(
            reverse("admin:catalog_product_bulk_images", args=[product.pk])
        )

        assert response.status_code == 403


class TestExportFormats:
    def test_excel_is_offered(self):
        """django-import-export only offers a format whose library is present;
        without openpyxl the dropdown silently listed no Excel at all."""
        from import_export.formats.base_formats import DEFAULT_FORMATS

        names = {fmt.__name__ for fmt in DEFAULT_FORMATS if fmt().can_export()}

        assert "XLSX" in names, f"Excel export is not available; formats={sorted(names)}"

    @pytest.mark.parametrize("format_index", [0, 1, 2])
    def test_every_exportable_admin_produces_a_file(
        self, admin_client_su, seeded_catalogue, format_index
    ):
        from import_export.admin import ExportMixin

        failures = []
        for model, model_admin in admin.site._registry.items():
            if not isinstance(model_admin, ExportMixin):
                continue
            try:
                url = reverse(
                    f"admin:{model._meta.app_label}_{model._meta.model_name}_export"
                )
            except NoReverseMatch:
                continue
            response = admin_client_su.post(
                url, {"format": str(format_index), "resource": "0"}
            )
            if response.status_code >= 400 or b"errorlist" in response.content:
                failures.append(f"{model._meta.label} -> {response.status_code}")

        assert not failures, f"export failed for: {failures}"


class TestUploadedMediaIsReachable:
    def test_media_is_served_even_with_debug_off(self, settings, admin_client_su, product):
        """The nginx /media/ alias is an example file that has to be installed by
        hand. When it is not, every uploaded image 404s while the page around it
        renders — so Django keeps a fallback (config/urls.py)."""
        settings.DEBUG = False
        url = reverse("admin:catalog_product_bulk_images", args=[product.pk])
        admin_client_su.post(
            url,
            {"images": [SimpleUploadedFile("m.png", png_bytes(), content_type="image/png")]},
            follow=True,
        )

        image = product.images.first()
        response = Client().get(image.image.url)

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "image/png"

    def test_it_refuses_a_path_that_escapes_media_root(self):
        response = Client().get("/media/../../etc/passwd")

        assert response.status_code in (400, 404)
