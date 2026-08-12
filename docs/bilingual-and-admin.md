# Bilingual storefront and staff administration

Handover notes for the two things added on top of the approved Arabic build:
a second language, and a set of fixes to the admin write paths.

---

## 1. Language: Arabic and English

Arabic is the source language. Every Arabic string is the *msgid* and English is
its translation, which means a missing translation degrades to correct Arabic
rather than to a blank or a key.

### How a visitor switches

A globe-icon switcher sits in the storefront header (and in the mobile menu),
and a matching one sits in the admin's top strip. Both are `POST` forms, not
links: switching writes a cookie, and a `GET` that changes stored state is
something a prefetching browser or a crawler will trigger without a human.

The choice is stored in the `zakey_language` cookie for a year.

**The public URLs did not move.** `i18n_patterns` is the usual answer and would
have prefixed every route with `/ar/` or `/en/`; the thirteen storefront URLs
are half of the route contract (FR-131), so the language lives in a cookie
instead of the path. Existing links, bookmarks and indexed results are unchanged.

### Two different things get translated

| What | Mechanism | Where you edit it |
|---|---|---|
| Interface copy — buttons, labels, headings baked into the pages | gettext catalogue | `locale/en/LC_MESSAGES/django.po` |
| Catalogue and content — product names, categories, FAQs, page copy | `_en` database columns | The Django admin |

That split matters: a product name changes without a developer, so it must be a
database field; a button label does not, so it belongs in a catalogue.

### Editing interface copy

```bash
uv run python manage.py sync_translations          # extract + compile
uv run python manage.py sync_translations --check  # fail if anything is untranslated
```

This does the job of `makemessages` + `compilemessages` **without GNU gettext**,
which is not installed on the deployment host. Existing translations in the
`.po` are always preserved; only the message list and source references are
regenerated. Implementation is in `apps/core/translations.py`.

After editing `locale/en/LC_MESSAGES/django.po`, re-run the command to rebuild
the binary `.mo` that Django reads, and restart the app.

### Editing catalogue copy

Every user-facing text field has an `_en` sibling, labelled `… (إنجليزي)` in the
admin. On the product form they are grouped into a collapsible **النسخة
الإنجليزية** section, so the Arabic form staff use daily stays short.

The fallback is **per field, not per record**. A product with an English name but
no English description renders the English name and the Arabic description —
never a blank.

The product changelist has an **الإنجليزية** column showing at a glance which
rows still read Arabic to an English visitor.

Models carrying `_en` columns: `Category`, `Brand`, `Collection`, `Product`,
`ProductVariant`, `ProductImage`, `ProductFeature`, `SpecificationGroup`,
`SpecificationItem`, `ProductDocument`, `HomeSection` (including a `data_en`
JSON overlay), `Banner`, `Partner`, `FAQ`, `StaticPage`, `NavigationItem`,
`Governorate`, `ServiceArea`, `ShippingMethod`, `InstallationService`,
`PaymentMethod`, `Coupon`, `Review`, `SiteSetting`.

`HomeSection.data_en` is a **sparse overlay**: translate only the keys that
matter and the rest deep-merges from the Arabic, so a partly translated page
section renders English where it has it and correct Arabic everywhere else.

To load English copy for the demonstration catalogue:

```bash
uv run python manage.py seed_english_demo
```

It only fills blanks, so it never overwrites a real translation. Pass
`--overwrite` to force.

### Layout direction

`<html dir>` follows the active language — `rtl` for Arabic, `ltr` for English —
on the storefront and in the admin. The stylesheet was already written in CSS
logical properties (`margin-inline-start`, `inset-inline-end`), so nothing had to
be mirrored by hand, and no direction-specific stylesheet exists.

Django ships its own Arabic and English admin catalogues, so the entire staff
console — labels, dates, layout — mirrors with the switch.

---

## 2. Admin fixes

### The 500

`payments.Refund` made every field read-only but still offered an **Add** button.
The form rendered only `reason`, so saving raised `IntegrityError` on the NOT
NULL `amount` — a guaranteed 500 behind a visible button.

Refunds are now issued from the payment they belong to, through the **استرجاع
مبلغ من الدفعات المختارة** action on the Payments changelist. That action goes
through `payments.services.refund`, which is the only path that checks the
refundable balance, moves the payment state with it, and writes an event and an
audit row.

`tests/security/test_admin_write_paths.py` carries a structural guard: no admin
may offer an Add form whose fields cannot satisfy the model's NOT NULL columns.

### The 404s

Uploaded media is served by nginx in production via the `/media/` alias in
`deploy/zakey-nginx.conf` — but that file is an example that has to be installed
by hand, and when it is not, every uploaded image 404s while the page around it
renders perfectly. That reads as a broken upload rather than a missing
web-server rule.

Django now keeps a fallback, on by default:

```
ZAKEY_SERVE_MEDIA=True    # set False once nginx is confirmed to serve /media/
```

Note `django.conf.urls.static.static()` is deliberately not used for it — that
helper returns an empty list whenever `DEBUG` is `False`, which is the one
environment that needs the fallback.

`MEDIA_ROOT` is also created at startup: an upload into a directory that does
not exist fails deep inside the storage backend and reaches staff as a bare 500.

### The 400s

`DATA_UPLOAD_MAX_NUMBER_FIELDS` was 1000. A product change form is six inline
formsets deep, and a well-stocked lock renders several hundred inputs before
staff type anything — close enough to be reachable, and the failure mode is a
400 on save with the edit lost. It is now 5000, and
`DATA_UPLOAD_MAX_NUMBER_FILES` is 500 for the bulk upload.

### Bulk image upload

A product's change form now carries a **رفع صور متعددة** link that accepts a
whole selection of files at once. Every file goes through the same
`validate_image_upload` the inline uses — signature checked against the file's
own bytes, SVG refused, decompression bombs capped — so it is a faster path to
the same guarantees, never a way around them.

One bad file rejects the whole batch and names it, rather than importing some
and leaving staff to work out which failed.

### Import and export

Excel export now works: `openpyxl` was missing, so the format dropdown silently
offered only CSV, TSV, JSON and HTML.

Coverage went from 6 exportable models to 24, and 4 importable to 15. The split
is deliberate:

- **Catalogue and configuration import and export** — product, variant, stock
  thresholds, coupon, category, brand, collection, feature, specification, FAQ,
  static page, navigation, governorate, service area, shipping rate. These are
  what a shop populates from a spreadsheet at launch and re-exports for a
  translator.
- **Financial and customer-written records export only** — order (by order and
  by line), payment, refund, review, customer profile, newsletter, contact
  message, stock ledger, audit log. There is no legitimate reason to *write* an
  order or a review from a spreadsheet, and offering the button would be
  offering a way to forge one.

The customer-profile export deliberately omits the phone number, which is gated
behind `accounts.view_full_contact` in the admin; an export carrying it would be
a way around that check.

---

## Verifying it

```bash
uv run python manage.py sync_translations --check    # every message translated
DJANGO_ENV=test uv run python -m pytest               # full suite
```

The bilingual behaviour is covered by `tests/integration/test_bilingual.py` and
the admin write paths by `tests/security/test_admin_write_paths.py`.
