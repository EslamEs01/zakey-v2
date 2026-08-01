# Frontend Fixture Contract

## Authority

`storefront/fixtures/frontend-fixtures.json` is the sole authored demonstration-data source.
Templates and JavaScript must consume adapter output and must not define product, price, tax,
shipping, payment, review, FAQ, account, cart or wishlist records independently.

## Adapter interface

### CatalogueCriteria

Normalized fields are `q: string`, `category: string|null`, `collection: string|null`,
`priceMin: integer|null`, `priceMax: integer|null`, `features: string[]`,
`availability: "available"|"unavailable"|null`, `sort: "featured"|"price-asc"|
"price-desc"|"name"`, and `page: positive integer`. Query parameters repeat `feature`; whitespace
is trimmed; unknown slugs/features/sorts are discarded; reversed price bounds are swapped; page
clamps after result count is known.

### CatalogueResult

`{criteria, products, totalCount, page, pageSize, pageCount, activeChips, state}` where `state` is
`populated | no-search-results | no-filtered-results | loading | recoverable-error`. Stable sorting
uses fixture order as the final tie-breaker. `activeChips` contain stable key, Arabic label and a
canonical removal URL.

### ProductDetailContext

`{product, relatedProducts, selectedImageId, selectedFinishId, prototypeNotice}`. Product is the
normalized field set in `data-model.md`; missing slug yields the page-level not-found outcome.

### PageStateContext

`{page, state, content, prototypeNotice}` where page/state must be a pair enumerated in
`qa-matrix.json`. Unknown explicit QA state falls back to the page default.

### ClientFixture

Contains shared settings, normalized catalogue/content records and default state only. It excludes
contact details not rendered publicly, filesystem paths, developer metadata and all secrets (none
are expected). Server and client catalogue algorithms must produce identical product ID order,
count and clamped page for canonical parity cases.

`get_site_context()` returns shared site/navigation/footer/localisation settings.

`get_catalogue(query)` accepts a Django QueryDict-compatible mapping and returns CatalogueResult.

`get_product(slug)` returns ProductDetailContext or raises the presentation-level not-found outcome.

`get_page_context(page, state)` returns PageStateContext without database/network access.

`get_client_fixture()` returns ClientFixture serialized through Django's safe JSON mechanism.

## Invariants

- Fixture status is `demonstration` and UI wording never claims verified production data.
- All IDs/slugs and 27 governorate keys are unique.
- All product references and local asset paths resolve.
- Prices are integer EGP values from 2190 through 7490.
- VAT, shipping threshold, coupon labels and service eligibility have one source.
- No credential, secret, provider identifier, real order/customer ID or remote asset URL exists.
- Adapter failures are deterministic developer errors, not silently patched in templates.

## Future replacement

A later backend adapter may satisfy the same normalized view-context shapes. That future work may
replace the source but must not require changing semantic page/component contracts. This contract
does not specify database schema, APIs or business services.
