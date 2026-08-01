# Browser Route Inventory

**Final status**: Pass.

The presentation shell exposes 13 public route families and 56 contracted states.
Every state passed in Chrome at 1440, 1024, 768 and 390 pixels, producing 224 browser
cells, 224 screenshots and 224 rendered HTML files.

| Route | Canonical URL | States | Cells | Browser result | Visual review |
|---|---|---:|---:|---|---|
| Home | / | 11 | 44 | Pass | Pass |
| Shop | /shop/ | 6 | 24 | Pass | Pass |
| Collection | /collections/smart-door-locks/ | 1 | 4 | Pass | Pass |
| Search | /search/?q=ذكي | 2 | 8 | Pass | Pass |
| Product | /products/zakey-apex-pro/ | 6 | 24 | Pass | Pass |
| Cart | /cart/ | 7 | 28 | Pass | Pass |
| Checkout | /checkout/ | 7 | 28 | Pass | Pass |
| Wishlist | /wishlist/ | 3 | 12 | Pass | Pass |
| Account | /account/?state=signed-in | 5 | 20 | Pass | Pass |
| About | /about/ | 1 | 4 | Pass | Pass |
| Contact | /contact/ | 5 | 20 | Pass | Pass |
| 404 | /errors/404/ | 1 | 4 | Pass, expected HTTP 404 | Pass |
| 5xx | /errors/500/ | 1 | 4 | Pass, expected HTTP 500 | Pass |
| **Total** |  | **56** | **224** | **Pass** | **Pass** |

Project-level 404 and 500 handlers use the same storefront error views. The explicit
error URLs are safe QA previews and intentionally preserve their non-200 status.

## Executed browser suites

| Suite | Result |
|---|---|
| tests/e2e/site-integrity.spec.js, all four projects | 224/224 passed |
| tests/e2e/no-js.spec.js, four no-JS projects | 40/40 passed |
| tests/e2e/interaction-journeys.spec.js, all four projects | 28/28 passed |

The site-integrity suite checks status, RTL, landmarks/headings, action postconditions,
axe, overflow, images, links, local assets, console/page errors, screenshots and
rendered DOM. The interaction journeys use visible controls rather than direct state
mutation for the material menu, filter, gallery, tab, checkout and account flows.
