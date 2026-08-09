"""Report what the signed-out account page renders (visual triage support)."""
import os
import re

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

client = Client()
body = client.get(reverse("storefront:account")).content.decode()

forms = re.findall(r'<form[^>]*?(data-[a-z-]+form)[^>]*>', body)
print("forms rendered on the signed-out account page:")
for name in forms:
    print(f"  {name}")
print(f"  total <form> elements: {body.count('<form')}")

for marker, label in [
    ("account-auth-card", "auth cards"),
    ("account-profile__name", "customer name block (must be absent signed-out)"),
    ("account-panel__note", "guest-checkout note"),
    ("account-tabs", "account tabs"),
    ("data-forgot-form", "forgot-password form"),
    ("data-reset-form", "set-new-password form"),
]:
    print(f"  {label}: {body.count(marker)}")

# Rough vertical proxy: count block-level elements inside the auth area.
auth = re.search(r'class="[^"]*account-auth[^"]*"(.*?)</section>', body, re.S)
if auth:
    chunk = auth.group(1)
    print(f"\n  auth area: {chunk.count('<form')} forms, "
          f"{chunk.count('<input')} inputs, {chunk.count('<label')} labels")
print(f"\n  total inputs on page: {body.count('<input')}")
print(f"  total labels on page: {body.count('<label')}")
