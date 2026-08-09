"""Report the checkout summary rows (visual triage support)."""
import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

client = Client()
response = client.get(reverse("storefront:checkout"))
body = response.content.decode()
print(f"status={response.status_code}")

rows = re.findall(r'<(?:li|div|tr)[^>]*summary-row[^>]*>(.*?)</(?:li|div|tr)>', body, re.S)
print(f"\nsummary rows found: {len(rows)}")
for row in rows:
    text = re.sub(r"<[^>]+>", " ", row)
    text = " ".join(text.split())
    if text:
        print(f"  {text[:90]}")

for marker in ["الشحن", "التركيب", "ضريبة", "الإجمالي", "الخصم", "المجموع"]:
    print(f"  contains {marker!r}: {body.count(marker)}")

print(f"\n  steppers rendered: {body.count('checkout-step')}")
print(f"  cart lines: {body.count('data-cart-line')}")
