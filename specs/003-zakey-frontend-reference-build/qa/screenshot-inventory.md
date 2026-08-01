# Screenshot Inventory

**Final status**: Complete.

The full binary evidence is retained in the local QA workspace and excluded from
Git because it is reproducible and large. This repository publishes the inventory,
reference measurements, QA matrices and review findings needed to reproduce and
audit those captures.

| Evidence | Directory | Count |
|---|---|---:|
| Live-reference screenshots | reference-evidence/screenshots/ | 53 PNG |
| Live-reference measurements | reference-evidence/measurements/ | 53 JSON |
| Implementation screenshots | qa/implementation-screenshots/ | 224 PNG |
| Rendered implementation DOM | qa/rendered-html/ | 224 HTML |

Implementation names follow routeId__stateId__width.ext. Each required width has 56
PNG and 56 HTML files. Route counts are Home 44, Shop 24, Collection 4, Search 8,
Product 24, Cart 28, Checkout 28, Wishlist 12, Account 20, About 4, Contact 20, 404
4 and 5xx 4.

The evidence validator passed with:

    QA matrix is complete: 56 states × 4 widths.

## Reference mapping notes

Twenty-one states have direct reference mappings; 35 have documented
referenceAbsentReason entries and extend the same shared grammar. Checkout Payment
has direct source captures only at 1440 and 390; the unavailable 1024 and 768 source
frames are documented rather than invented. Six probing captures are retained as
inspection evidence but are not treated as accepted state references.

Codex compared the core pairs for Home, Shop, search, Product, empty/populated Cart,
Checkout Shipping/Payment, Account, About, Contact, mobile menu/filter, Product
Specifications and Product FAQ. Both visual passes are recorded in
visual-comparison-findings.md.
