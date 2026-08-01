# Contract: Template View Models

**Feature**: `001-premium-storefront-experience`
**Contract ID**: `C-VIEWMODEL`

## Why this contract exists

The specification requires that public templates survive the Feature 002 catalogue swap unchanged.
A port on the data side (`C-CATALOG`) is not sufficient on its own: if templates consume provider
types directly, replacing the provider still reshapes every template.

**This contract is the second half of the insulation.** Templates consume **view models** — plain,
presentation-shaped, provider-agnostic structures assembled in the view layer. A template never sees
a `Product`, a JSON dict, a Django model, or any provider type.

```
governed JSON  →  loader  →  Product (Tier A)  →  view assembles ProductCardVM  →  template
                                     ↑                                              ↑
                            swapped in Feature 002                    unchanged in Feature 002
```

## Binding rules

1. A template may reference **only** attributes declared on a view model in this document.
2. A view model exposes **display-ready values**. No template performs price formatting, availability
   logic, total computation, or provenance interpretation.
3. A view model MUST NOT expose the provider, the loader, a file path, a raw dataset dict, or a
   Django model instance.
4. Money is pre-formatted into a string **or** is `None`. A template can therefore never render a
   partial or malformed price, and cannot compute one.
5. Every product-bearing view model carries supplier attribution as a **non-optional** field, so a
   product cannot be rendered without it (FR-111, SC-041).

## Core view models

### `ProductCardVM` — every grid, rail, wishlist row, and related item

```
slug                  str
name                  str
supplier_line         str          # e.g. "by Lezn" — non-optional
category_name         str
image                 ImageVM
url                   str          # reversed from a named route; never hand-built
price_display         str | None   # formatted string, or None
price_on_request      bool         # True ⇒ render the price-on-request statement
in_wishlist           bool
in_cart               bool
badges                tuple[BadgeVM, ...]   # verified attributes only
```

`price_display` and `price_on_request` are **mutually exclusive and both pre-decided**. The template
branches on a boolean; it never inspects a price object, so it cannot accidentally render `None`,
`0`, or a currency-less number.

`badges` may carry only category, collection, access-method, or supplier attribution. Popularity,
discount, award, certification, "Sale", and "New" badges have no representation here — a fabricated
badge cannot be expressed (FR-038, RD-7).

### `ImageVM`

```
src                str       # 1× rendition
srcset             str
sizes              str
width              int       # intrinsic — always present (PB-14)
height             int       # intrinsic — always present
alt                str       # derived, meaningful, never internal terminology
loading            "lazy" | "eager"
fetchpriority      "high" | "auto"
is_placeholder     bool      # True ⇒ proportioned placeholder, never a broken image
```

`width` and `height` are non-optional, so every image reserves space and CLS cannot be introduced by
omission (PB-14, NFR-030). `is_placeholder` implements FR-041 — a missing asset renders a correctly
proportioned region with meaningful alt text rather than a broken-image icon.

### `ProductDetailVM`

```
slug, name, supplier_line, summary, product_type   str
category            TaxonomyLinkVM
collections         tuple[TaxonomyLinkVM, ...]     # may be empty — 9 of 21 products
access_methods      tuple[TaxonomyLinkVM, ...]
gallery             GalleryVM
price_display       str | None
price_on_request    bool
availability_text   str          # enquiry-based; never a stock count
specifications      tuple[SpecRowVM, ...]          # populated fields only
attribution_note    str          # ZAKEY-as-retailer statement (FR-040, CI-8)
actions             tuple[ActionVM, ...]
related             tuple[ProductCardVM, ...]
breadcrumbs         tuple[CrumbVM, ...]
```

`specifications` contains only populated allowlisted fields — an unpopulated field is **absent from
the tuple**, so a template iterating it cannot emit an empty row (FR-035).

`SpecRowVM { label, value, source_page }` carries the page citation, keeping every technical claim
traceable.

### `GalleryVM`

```
images        tuple[ImageVM, ...]
has_multiple  bool     # False ⇒ template renders no controls at all (FR-033)
```

`has_multiple` prevents the disabled-carousel failure mode: single-image products render without
gallery navigation rather than with inert controls.

### `CartVM` / `CartLineVM`

```
CartVM
  lines               tuple[CartLineVM, ...]
  is_empty            bool
  line_count          int
  total_display       str | None    # None when not computable
  totals_computable   bool
  price_note          str | None    # price-on-request statement when not computable
  can_checkout        bool
  checkout_blocked_reason  str | None   # stated reason for a disabled control (FR-082)

CartLineVM
  slug, name, supplier_line   str
  image                       ImageVM
  qty                         int
  qty_min, qty_max            int          # 1, 99 — rendered as real input bounds
  line_total_display          str | None
  price_on_request            bool
  update_url, remove_url      str
```

`total_display is None` **and** `totals_computable is False` together make a misleading total
unrenderable. The template has no arithmetic and no fallback branch that could invent one
(FR-098, SC-040).

### `OrderReviewVM`

```
lines                tuple[CartLineVM, ...]
information_groups   tuple[InfoGroupVM, ...]   # escaped values + edit links
total_display        str | None
totals_computable    bool
disclosure           str    # "No order has been placed and no payment has been taken." (FR-107)
actions              tuple[ActionVM, ...]      # exactly EDIT_CART, EDIT_INFORMATION, SEND_ENQUIRY
```

`disclosure` is **non-optional**. The review page cannot render without stating that no order was
placed and no payment taken.

### `FormVM` / `FieldVM`

```
FieldVM
  name, label, value, input_type   str
  required            bool
  autocomplete        str
  errors              tuple[str, ...]
  described_by_id     str | None   # wires the error to the field (A-8)
  invalid             bool
  placeholder         str | None   # rendered in #6B7280, never #9CA3AF (FR-120)

FormVM
  fields              tuple[FieldVM, ...]
  form_errors         tuple[str, ...]
  first_invalid_field str | None
  submitting          bool
  action_url, csrf_required
```

`label` is non-optional, so a field cannot render without a visible label (FR-054, A-7).
`described_by_id` makes the error/field association structural rather than something a template
author must remember.

### `PaginationVM`, `FilterPanelVM`, `SortVM`

```
PaginationVM   { current, total_pages, has_prev, has_next, prev_url, next_url,
                 pages: tuple[PageLinkVM,...], is_single_page }
FilterPanelVM  { groups: tuple[FilterGroupVM,...], applied: tuple[AppliedFilterVM,...],
                 clear_all_url, has_any_applied }
SortVM         { options: tuple[SortOptionVM,...], selected }
```

Every URL is pre-reversed with query state already encoded, so templates never build URLs by string
concatenation (FR-077). `SortVM.options` cannot contain a price or popularity option because
`SortOption` has no such member (C-CATALOG).

`AppliedFilterVM` carries a `remove_url` that drops exactly one filter, implementing FR-019.

### `LayoutVM` — supplied to every page by one context processor

```
nav_items          tuple[NavItemVM, ...]     # each with is_current (FR-008)
cart_count         int
wishlist_count     int
announcement       AnnouncementVM | None     # None ⇒ bar absent, layout still correct (FR-002, FR-090)
footer_groups      tuple[FooterGroupVM, ...] # links only to pages that exist (FR-012)
search_action_url  str
skip_link_target   str
```

`footer_groups` is assembled from the route table, so a link to a non-existent page cannot be
rendered — closing FR-012 and SC-004 structurally rather than by review.

## Enforcement

1. **Template audit** — an automated check parses every template and fails on any attribute access
   not declared in this contract, and on any reference to provider internals, dataset paths, or
   model instances.
2. **View-model unit tests** — assert `price_display is None` whenever `price_on_request` is `True`,
   that `supplier_line` is never empty, and that `ImageVM.width/height` are always set.
3. **Feature 002 rehearsal test** — renders every template against view models built from a fake
   provider whose backing store is *not* the JSON, proving templates are provider-agnostic before
   Feature 002 begins.
