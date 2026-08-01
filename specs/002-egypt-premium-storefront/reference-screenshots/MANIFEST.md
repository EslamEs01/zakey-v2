# Reference Screenshot Manifest — Specification 002

**Captured**: 2026-08-01
**Reference**: `https://remote-fried-86528699.figma.site/` (HTTP 200)
**Method**: Real browser — Chromium 148.0.7778.97 via Playwright 1.61.1, `deviceScaleFactor: 1`, `fullPage: true`
**Total files**: 35

The Figma Make publishing overlay ("Created with Figma Make" / "Remix") was hidden before every
capture because it is hosting chrome, not part of the design under inspection. Nothing else was
modified.

## Integrity policy applied to this set

Every capture was verified against its measured DOM state before being kept. Captures whose
labelled identity could not be defended — where navigation did not actually reach the named route
— were **deleted rather than retained under a misleading name**. Eight files were removed on that
basis (`about-390/768`, `contact-390/768`, `shop-390/768`, `cart-filled-390/768`); each had been
proven by content hash and DOM heading to be a different page from its label.

## Coverage by viewport

| Viewport | Class | Files |
| --- | --- | --- |
| 1440px | Desktop reference | 11 |
| 1024px | Tablet | 12 |
| 768px | Transition | 7 |
| 390px | Mobile | 5 |

## Files and verified content

| File pattern | State captured | Verification |
| --- | --- | --- |
| `home-{1440,1024,768,390}.png` | Home, full page | 14-band landing page. docH 7195 / 7053 / 11062 / 14747 |
| `catalog-via-view-{1440,1024,768,390}.png` | Catalog ("All Products"), reached via a product "View" control | DOM `h1` = "All Products" at **all four widths**. docH 2574 / 2942 / 3360 / 6004. **Overflow measured at 390** |
| `shop-{1440,1024}.png` | Catalog, reached via header "Shop" | Byte-identical to `catalog-via-view-{1440,1024}.png` — this is the **proof** that a product "View" control routes to the catalog, not to a product page |
| `cart-{1440,1024,768,390}.png` | Cart route | "Shopping Cart (0 items)" — empty state only |
| `cart-filled-{1440,1024}.png` | Cart after an Add-to-Cart attempt | Byte-identical to `cart-{1440,1024}.png` — the **proof** that the reference never produces a populated cart |
| `account-{1440,1024,768}.png` | Account | Signed-in stub, fabricated identity and order history, no login/registration |
| `search-{1440,1024,768,390}.png` | Search open | Inline expanding bar (+62px), not a modal |
| `wishlist-{1440,1024,768}.png` | Wishlist control activated | No state change — the control is inert |
| `menu-open-{1024,768,390}.png` | Mobile navigation open | Inline header expansion (+205px), no dialog role, no focus trap |
| `products-menu-{1440,1024}.png` | "Products" dropdown | 4 entries, 190×40 each |
| `about-{1440,1024}.png` | About | "Built on Trust, Driven by Innovation" + fabricated statistics |
| `contact-{1440,1024}.png` | Contact | US/Singapore contact data, 5-field unlabelled form, invented FAQ claims |

### Why there is no product-details capture

The reference has **no product-details page**. Activating any product "View" control routes to the
catalog. This was proven three ways: identical document height (2574px at 1440), an identical
control set including "Clear All Filters", and a DOM `h1` of "All Products". The
`catalog-via-view-*` files are retained as evidence **of that absence** and simultaneously serve as
the catalog's own grounding at 768 and 390.

## Coverage gaps (declared, not hidden)

| Gap | Reason | Effect on the specification |
| --- | --- | --- |
| `about` and `contact` at 768px and 390px | At ≤1024px the navigation collapses to a hamburger; navigation to those routes from the open mobile panel did not resolve in this pass. Captures produced under those labels were proven to be a different page and were deleted. | About and Contact are grounded at **1440 and 1024 only**. Their 768/390 layout requirements derive from the home page's verified transformations at those widths and are marked **evidence-based adaptation** in `reference-fidelity-matrix.md`. Recorded as precondition RP-07. |
| `account` at 390px | Not captured in this pass | Account is grounded at 1440/1024/768; its 390 layout is an evidence-based adaptation. |
| Checkout, login, registration | **Do not exist** in the reference | Specified as evidence-based compositions of inspected components. |
| Hover / active / disabled pseudo-states | Not reliably capturable in a headless full-page pass | Requirements derive from ratified tokens and Principle VIII contrast rules, not from reference grounding. |

## Measured facts captured alongside the screenshots

Container widths, header geometry, band order with background colours, grid column counts and
gaps, typography scale, colour census, radius census, shadow census, image intrinsic vs displayed
sizes, control inventories, input labelling status, and horizontal-overflow assertions — all
summarised in `visual-reference-inventory.md`.
