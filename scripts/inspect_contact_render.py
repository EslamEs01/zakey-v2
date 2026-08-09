"""Report which contact-page blocks actually render (visual triage support)."""
import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

client = Client()
body = client.get(reverse("storefront:contact")).content.decode()

checks = {
    "page heading (contact.heading)": r'id="contact-title">\s*([^<]*)</h1>',
    "eyebrow (contact.eyebrow)": r'class="eyebrow">\s*([^<]*)</p>',
    "form heading (contact.form.heading)": r'id="contact-form-title">\s*([^<]*)</h2>',
    "submit label (contact.form.submitLabel)": r'type="submit"[^>]*>\s*([^<]*)<',
    "chat card heading (contact.chatCard.heading)": r'<h3>\s*([^<]*)</h3>',
}

print("contact page rendered blocks:")
for label, pattern in checks.items():
    match = re.search(pattern, body)
    value = (match.group(1).strip() if match else None)
    state = "EMPTY" if value == "" else ("MISSING" if value is None else "ok")
    print(f"  [{state:7s}] {label}: {value!r}")

method_cards = body.count("contact-method")
faq_details = len(re.findall(r'<details class="contact-faq__item"', body))
static_faq = len(re.findall(r'<div class="contact-faq__item"', body))
print(f"\n  method cards rendered: {method_cards}")
print(f"  database FAQ <details> rendered: {faq_details}")
print(f"  hard-coded FAQ blocks rendered: {static_faq}")

from apps.content.models import FAQ  # noqa: E402

print(f"  FAQ rows in DB for page='contact': "
      f"{FAQ.objects.filter(is_active=True, page='contact').count()}")
print(f"  total active FAQ rows: {FAQ.objects.filter(is_active=True).count()}")
