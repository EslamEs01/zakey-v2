# Contract: Storefront Data Contract

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-130, FR-131.

The backend must satisfy the **same template context shapes** the fixture provider produces today. Templates are the consumer; keeping this contract is what makes integration a view-layer change rather than a template rewrite.

---

## 1. Global context (every page)

Produced today by `fixture_provider.get_site_context()` (`fixture_provider.py:270-278`).

| Key | Today | After |
|---|---|---|
| `site` | fixture `site` dict | `SiteSetting` + content models |
| `navigation` | fixture `navigation` | `NavigationItem` grouped `primary`/`utility`/`footer` |
| `categories` | list of 4 | published `Category` queryset |
| `collections` | list of 6 | published `Collection` queryset |
| `client_fixture` | 14 fixture sections | **shrinks to presentation-only data** (FR-133) |
| `page_id`, `page_state` | strings | unchanged |

New keys added by integration: `cart_count`, `wishlist_count`, `user` / `customer`.

`client_fixture` is the biggest reduction: today it ships the whole catalogue to the browser so JS can filter it (`get_client_fixture`, L280-289). Once the server owns filtering, only presentation data (labels, notices, area lists for the address form) remains.

---

## 2. Catalogue context

`get_catalogue(query, collection=None)` → `CatalogueResult`. Keys **must not change**:

```
criteria      CatalogueCriteria (q, category, collection, price_min, price_max,
                                 features, availability, sort, page)
products      list — each with .category attached
totalCount    int
page          int (clamped)
pageSize      int — 6
pageCount     int (min 1)
activeChips   list of {key, value, label}   ← Arabic labels
filterFeatures list of {key, label}
state         populated | no-search-results | no-filtered-results
```

**Behavioural parity required** (T-0509 asserts it):

| Rule | Source |
|---|---|
| Page size 6 | `fixture_provider.py:196`, `catalogue.js:4` |
| Sorts: `featured`, `price-asc`, `price-desc`, `name`; unknown → `featured` | `:12,138` |
| Stable tie-break by original order | `:203-210` |
| `availability=available` matches `available` **and** `limited` | `:183-190` |
| Feature facets use **AND** semantics | `:167-172`, `catalogue.js:55` |
| Search over `name` + `shortDescription`, case-folded | `:159-166` |
| Reversed price bounds swapped | `:121-124` |
| Unknown slug/feature/sort discarded | `:129-138` |
| Page clamped after filtering | `:199-201` |
| `state` = `no-search-results` when a query and no filters; else `no-filtered-results` | `:214-216` |

---

## 3. Product detail context

`get_product(slug)` → keys `product`, `relatedProducts`, `reviews`, `faqs`, `selectedImageId`, `selectedFinishId`, `prototypeNotice`.

Product object must expose, at minimum: `id`, `slug`, `name`, `shortDescription`, `price`, `compareAtPrice`, `badge`, `rating`, `reviewCount`, `availability`, `images[]` (`id`, `path`, `width`, `height`, `alt`), `finishes[]` (`id`, `label`, `swatch`), `features[]` (`key`, `label`, `description`), `specificationGroups[]`, `downloads[]`, `instalmentMessage`, `serviceFlags`, `category`.

`selectedImageId` = first image, `selectedFinishId` = first finish (`:267-268`) — so **every product must have ≥1 of each** (FR-015).

Missing slug → the existing 404 outcome, not an exception.

---

## 4. Page-specific context

| Page | Keys |
|---|---|
| home | `best_sellers` (4), `featured` (4), `home_reviews` (3) — derived from collection membership and review `placement`, `views.py:17-19` |
| cart | + `cart`, `totals` (server-computed) |
| checkout | `checkout_step` ∈ {shipping, payment, review} + `governorates`, `areas`, `shipping_options`, `payment_options`, `totals` |
| wishlist | + `wishlist` |
| account | `account_mode`, `account_tab` → real session + the 5 tabs (`account.js:3`) |

---

## 5. Rules

1. **Context keys are the contract.** Renaming one is a template change and needs the visual gate.
2. **Money arrives pre-computed and pre-quantized** — templates never do arithmetic.
3. **Arabic labels come from the server** — templates never build them from ids.
4. **Availability is derived**, never a stored free-text field.
5. **Ordering is explicit** — images, finishes, features, specs, collection membership all carry `position`.
6. **Absent data renders the existing empty state**, never a blank region or an exception.
7. **No new template variable may be introduced** where an existing key can carry the value.
