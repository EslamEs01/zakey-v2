"""Contact and newsletter forms actually persist (T-1206, FR-098).

Both used to validate in the browser, fake a delay and report success while
saying, accurately, that nothing had been sent. A form that reports success
without storing anything is worse than no form: the visitor believes they have
been heard.
"""

from __future__ import annotations

import pytest
from django.urls import reverse

from apps.content.models import ContactMessage, NewsletterSubscription

pytestmark = pytest.mark.django_db

VALID_CONTACT = {
    "name": "ندى إبراهيم",
    "email": "nada@example.com",
    "phone": "01012345678",
    "subject": "product",
    "message": "أريد الاستفسار عن قفل زاكي أبيكس برو وتوافقه مع باب خشبي.",
}


def test_contact_message_is_stored(storefront):
    storefront.post(reverse("storefront:contact-send"), VALID_CONTACT, follow=True)

    message = ContactMessage.objects.get()
    assert message.email == "nada@example.com"
    assert message.subject == "product"


def test_short_message_is_rejected(storefront):
    """The storefront's own 20-character rule, enforced server-side."""
    response = storefront.post(
        reverse("storefront:contact-send"), {**VALID_CONTACT, "message": "قصيرة"}
    )
    assert not ContactMessage.objects.exists()
    assert "20" in response.content.decode()


def test_invalid_email_is_rejected(storefront):
    storefront.post(reverse("storefront:contact-send"), {**VALID_CONTACT, "email": "nope"})
    assert not ContactMessage.objects.exists()


def test_honeypot_submission_is_dropped(storefront):
    """A bot fills every field it finds, including the hidden one."""
    storefront.post(
        reverse("storefront:contact-send"), {**VALID_CONTACT, "company": "spam-co"}
    )
    assert not ContactMessage.objects.exists()


def test_newsletter_subscription_is_stored(storefront):
    storefront.post(
        reverse("storefront:newsletter"), {"email": "Nada@Example.com "}, follow=True
    )
    subscription = NewsletterSubscription.objects.get()
    assert subscription.email == "nada@example.com", "address was not normalised"


def test_resubscribing_is_not_an_error_and_not_a_duplicate(storefront):
    for _ in range(3):
        storefront.post(
            reverse("storefront:newsletter"), {"email": "nada@example.com"}, follow=True
        )
    assert NewsletterSubscription.objects.count() == 1


def test_newsletter_honeypot_is_dropped(storefront):
    storefront.post(
        reverse("storefront:newsletter"),
        {"email": "bot@example.com", "company": "spam-co"},
        follow=True,
    )
    assert not NewsletterSubscription.objects.exists()


def test_invalid_newsletter_email_is_rejected(storefront):
    storefront.post(reverse("storefront:newsletter"), {"email": "not-an-email"}, follow=True)
    assert not NewsletterSubscription.objects.exists()


def test_contact_page_renders_the_real_post_form(storefront):
    body = storefront.get(reverse("storefront:contact")).content.decode()
    assert reverse("storefront:contact-send") in body
    assert 'method="post"' in body
    assert "csrfmiddlewaretoken" in body
