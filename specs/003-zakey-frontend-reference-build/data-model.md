# Frontend Fixture and UI State Model

This document defines presentation fixtures and browser-local prototype state only. It does not
define or authorize Django models, database tables, migrations, orders or customers.

## Fixture root

`FrontendFixture` contains `meta`, `site`, `navigation`, `categories`, `collections`, `products`,
`reviews`, `faqs`, `partners`, `team`, `governorates`, `serviceEligibility`, `shippingOptions`,
`paymentOptions`, `prototypeAccounts`, `prototypeCarts` and `prototypeWishlists`.

`meta.fixtureStatus` must equal `demonstration`; the UI exposes a concise prototype notice where
commerce/account claims could otherwise be misunderstood.

## Entities

### SiteSettings

- `brand`, `locale`, `direction`, currency label and decimal policy
- VAT rate `0.14`, free-shipping threshold `1500`
- announcement, contact, newsletter and footer content
- prototype notice and reset label

### Category / Collection

- stable `id`, URL-safe `slug`, Arabic `name`, description and local image
- category type/count metadata derived from products, never manually duplicated
- collection has ordered `productIds` and a promotion treatment

### Product

- `id`, `slug`, Arabic name, category ID, collection IDs
- integer EGP `price`, optional `compareAtPrice`, badge, rating/count
- availability enum: `available | unavailable | limited`
- ordered local images with dimensions/alternative text
- finish choices, features, specification groups, prototype downloads, FAQ/review IDs
- related product IDs, instalment message and service flags

Rules: price is 2190–7490; related IDs exist and exclude self; unavailable disables purchase;
all referenced media must exist locally.

### Review / FAQ / Partner / TeamMember

Stable IDs and Arabic content. Reviews include prototype attribution and rating 1–5. Partner marks
have local assets or typographic fallbacks. Team content makes no unsupported operational claim.

### Governorate / ServiceEligibility

- each canonical governorate has stable normalized key and Arabic label exactly once
- `sameDayAreaKeys`: exact configured Greater Cairo area keys
- `installationGovernorateKeys`: `cairo`, `giza`, `alexandria`
- areas carry governorate key, Arabic label and eligibility flags

### ShippingOption / PaymentOption

Stable ID, Arabic label, description, prototype notice, eligibility keys and UI icon. These are
labels/options only and never provider connections.

### PrototypeAccount

`signed-out` or `signed-in`; signed-in identity has Arabic name, local contact/profile fields,
addresses and presentation-only order-history rows. An order-history row is inert fixture content,
not a created order.

## Browser state

### CartState

Version, line items (`productId`, `quantity`, `finishId`), coupon state and timestamp. Quantity is
1–9. Totals are derived, never persisted. Coupon enum: `idle | loading | accepted | rejected |
recoverable-error`.

### WishlistState

Version and unique product IDs. Unavailable products may remain saved but cannot be purchased.

### AccountDemoState

Version, mode (`signed-out | signed-in`) and selected tab. No credential or auth token exists.

### CheckoutState

Memory-only current step (`shipping | payment | review`), field values, field errors, shipping,
installation and payment choice. It has no order ID, paid flag, submission result or server write.

### UIState

Open drawer/dialog, selected tab/gallery image, loading, empty, validation and recoverable-error
flags. Modal state records trigger/focus restoration. It is not durable.

## State transitions

- Add available product → sanitized CartState → header count/status announcement.
- Toggle wishlist → unique WishlistState → all card/detail instances synchronize.
- Change filter/query/sort/page → URL/controls/results synchronize; invalid page clamps to 1.
- Shipping valid → Payment; invalid → remain Shipping and focus error summary/first invalid field.
- Payment selected → Review; Review action → explanatory unavailable-submission state only.
- Reset prototype → remove only namespaced ZAKEY keys and reload fixture defaults.

## Validation

The fixture adapter fails fast in development for duplicate IDs/slugs, missing references,
out-of-range prices/ratings, invalid asset paths, duplicate/missing governorates, unsupported
eligibility keys or missing prototype labels. Browser storage ignores unknown keys and falls back
to safe fixture defaults.
