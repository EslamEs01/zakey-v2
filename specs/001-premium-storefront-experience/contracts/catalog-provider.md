# Contract: Catalog Provider Port

**Feature**: `001-premium-storefront-experience`
**Contract ID**: `C-CATALOG`
**Stability**: Stable across Feature 001 → Feature 002. Breaking this contract is a Feature 002
migration event requiring a specification amendment.

## Purpose

This is the **only** way any view, template, or component may obtain product data. It exists so the
Feature 001 static verified-catalogue snapshot can be replaced by production database models in
Feature 002 without editing a single template, route, product card, search page, cart surface, or
checkout surface.

**Binding rule.** No template, template tag, context processor, or JavaScript module may import,
read, parse, or reference the underlying catalogue JSON file, its path, its loader, or any
provider-internal type. Templates receive **view models** (`C-VIEWMODEL`) only. A template that can
name the storage format is a contract violation and a build failure (see Enforcement).

## Port definition

```
CatalogProvider  (abstract; Feature 001 impl = StaticCatalogProvider,
                  Feature 002 impl = DatabaseCatalogProvider)

  list_products(query: ProductQuery) -> ProductPage
  get_product(slug: str) -> Product | None
  get_related(slug: str, limit: int) -> Sequence[Product]
  list_categories() -> Sequence[Category]
  get_category(slug: str) -> Category | None
  list_collections() -> Sequence[Collection]
  get_collection(slug: str) -> Collection | None
  list_access_methods() -> Sequence[AccessMethod]
  get_facet_counts(query: ProductQuery) -> FacetCounts
  get_homepage_products(role: str, limit: int) -> Sequence[Product]
  resolve_lines(refs: Sequence[LineRef]) -> LineResolution
  health() -> ProviderHealth
```

Every method is **read-only**. The port declares no create, update, or delete operation, so no
caller can mutate the catalogue — the static adapter is structurally incapable of it.

## Query object

```
ProductQuery
  search:            str | None        # free text; case- and accent-insensitive
  category_slugs:    frozenset[str]    # OR within facet
  collection_slugs:  frozenset[str]    # OR within facet
  access_method_slugs: frozenset[str]  # OR within facet
  sort:              SortOption        # FEATURED | NAME_ASC | NAME_DESC
  page:              int               # 1-based
  page_size:         int               # default 12
```

Facets combine with **AND** across families and **OR** within a family (FR-018). An empty query
returns the full catalogue in featured order.

`SortOption` deliberately has **no price or popularity member**. Price and popularity sorts cannot
be requested because they cannot be represented — enforcing FR-017 and FR-022 at the type level
rather than by validation. Feature 002 adds members when verified price data exists.

## Result objects

```
ProductPage
  items:        Sequence[Product]
  total_count:  int
  page:         int
  page_size:    int
  total_pages:  int
  has_previous: bool
  has_next:     bool

FacetCounts
  categories:      Mapping[str, int]
  collections:     Mapping[str, int]
  access_methods:  Mapping[str, int]
```

`FacetCounts` reflects counts **under the currently applied query**, so a facet that would yield
zero results can be shown as unavailable rather than leading to a dead end.

## Price representation — the integrity-critical rule

```
PriceAvailability = VERIFIED_PRICE | PRICE_ON_REQUEST

Product.price: VerifiedPrice | None
VerifiedPrice
  amount_minor: int          # integer minor units; never a float
  currency:     str          # ISO 4217
  source_ref:   str          # provenance of the verified price
```

**Verified prices are permitted. Unverified prices are not. The distinction is provenance, not
presence.**

- **A valid verified price MUST NOT cause the loader to fail.** When a product carries a price whose
  provenance is verified, the loader accepts it, `PriceAvailability` becomes `VERIFIED_PRICE`, and
  the priced surfaces activate. Nothing about the architecture assumes prices are absent.
- `Product.price is None` ⇒ `PRICE_ON_REQUEST` ⇒ the product is **enquiry-only**. **All 21 products
  in the current governed dataset are in this state**, because `retail_price` and `currency` are
  `null` on all 21.
- A provider MUST NOT synthesise, estimate, default, or zero-fill a price. There is no fallback
  value: absence means enquiry-only, never zero and never "from" (FR-034, FR-113, CI-5).
- Monetary amounts are integer minor units. Floats are prohibited to avoid representation error in
  totals.

### Current state: the Feature 001 launch catalogue is ENQUIRY-ONLY

**No launch product has a verified sellable price. None has any price value at all.** Verified by
structured inspection of the governed registers on 2026-08-01:

| Evidence | Result |
| --- | --- |
| Catalogue `retail_price` / `currency`, all 21 products | distinct values = `{(null, null)}` |
| Source register `source_price_raw` / `_min` / `_max` / `_currency` for the 21 launch records | **null on all 21** |
| The only non-null price field on the 21 launch records | `source_price_kind: "supplier_reference"` — a **classification label, not a price** |
| Source records elsewhere in the register that do carry amounts | 88 of 209, all `supplier_reference`, expressed as ranges such as `"$53~$56"` in USD — **none belongs to a launch product** |

Two independent reasons these supplier-reference amounts may never be published, even for
non-launch records:

1. They are **supplier reference/wholesale figures**, not sellable retail prices. The governed
   catalogue's own policy states it "creates no retail price, currency, discount … fact".
2. `source_price_*` is **not among the five allowlisted publishable specification fields**, so the
   loader never reads it (FR-035).

**Consequence: every product surface in Feature 001 is enquiry-only today.** The
`PRICE_ON_REQUEST` path is the live path; the `VERIFIED_PRICE` path is implemented and tested
against fixtures so it activates without redesign when real prices arrive.

### Governed source artifacts: exactly THREE

**There are three governed source registers, not four.** No verified-price artifact exists.

An earlier revision of this contract described a "digest-pinned verified-price manifest" in terms
that implied it already existed. **It does not exist.** It is defined below as a *controlled future
extension* — a specification of what such an artifact would have to satisfy **if and when** verified
prices are supplied. Nothing in Feature 001 depends on it, and its absence creates no unresolved
implementation decision.

### Controlled future extension — how a verified price would reach the provider

The governed catalogue schema types `retail_price` and `currency` as `"type": "null"`, so a price
cannot be expressed in that file. **When** verified sellable prices are supplied, they arrive by
exactly one of two routes, each carrying provenance:

1. **A verified-price register** — a new, digest-pinned artifact keyed by `source_record_id`, each
   entry carrying `amount_minor` (integer minor units), `currency` (ISO 4217), and a `source_ref`
   recording where the price was verified and by whom. Adding it makes the governed source inventory
   **four** artifacts, and requires a specification amendment recording the new artifact, its schema,
   and its digest.
2. **A schema-version bump** of the governed catalogue permitting non-null price values with
   provenance fields attached.

Either way the rule is identical: **a price is accepted only with provenance, and rejected without
it.** An unauthorised non-null price is a fail-closed condition (FC-3); a properly provenanced price
is accepted normally and **must not** cause a failure.

**Enquiry-only products may never produce a fabricated figure.** A product in `PRICE_ON_REQUEST`
contributes **no line total**, and its presence in a cart forces `Totals.computable = False` so that
**no cart total and no order-review total is rendered at all** (FR-098, FR-050, SC-040). A mixed cart
of priced and unpriced products presents per-line totals for the priced lines only and **no overall
monetary total**, because a partial total presented as a total would be misleading.

## Line resolution — the single source of truth for money

```
LineRef        { sku: str, qty: int }
LineResolution
  lines:        Sequence[ResolvedLine]
  dropped_skus: Sequence[str]        # unknown/withdrawn; caller drops silently
  totals:       Totals

ResolvedLine
  product:     Product
  qty:         int
  line_total:  Money | None          # None when the product is PRICE_ON_REQUEST

Totals
  computable:        bool            # False if ANY line lacks a verified price
  subtotal:          Money | None    # None when computable is False
  unpriced_count:    int
  currency:          str | None
```

**`resolve_lines` is the only place a monetary total may be computed anywhere in the system**
(FR-099, Constitution VI.8). Cart, wishlist-to-enquiry, checkout, order review, and the enquiry
surface all call it. Two surfaces therefore cannot disagree, because there is only one computation.

`Totals.computable` is `False` if **any** line is `PRICE_ON_REQUEST`; `subtotal` is then `None` and
callers MUST render the price-on-request statement instead of a figure (FR-098, FR-050, SC-040).
This makes a misleading total structurally impossible rather than merely discouraged.

`dropped_skus` implements stale-entry handling (FR-101, FR-047): the caller removes them, corrects
counts, and shows no error.

## Provenance — never lost in transit

Every `Product` carries, and every product-facing view model exposes:

```
supplier_brand:        str    # e.g. "Lezn"
supplier_relationship: str    # e.g. "supplier-branded_not-zakey-manufactured"
source_model_code:     str
identity_grounding:    str
```

`supplier_brand` and `supplier_relationship` are **non-optional**. A provider cannot return a
product without attribution, so a template cannot render one without it (FR-111, FR-112, SC-041).
ZAKEY is presented as the retailer; no code path can present a supplier product as
ZAKEY-manufactured.

## Specification fields

```
Product.specifications: Mapping[str, str]   # approved fields only, populated values only
```

Only the five approved specification fields may appear, and a field with no verified value is
**absent from the mapping** rather than present-and-empty — so a template iterating the mapping
cannot render an empty row (FR-035).

## Failure behaviour

| Condition | Contract behaviour |
| --- | --- |
| Unknown product slug | `get_product` returns `None`; view raises `Http404` → custom 404 (FR-086) |
| Unknown category/collection slug | `None` → `Http404` (FR-086) |
| Page beyond last | `ProductPage` clamped to the last valid page; never an exception (FR-088) |
| Empty/whitespace search | Treated as no search; MUST NOT present a results page implying a search occurred (FR-027) |
### Fail-closed startup conditions (complete list)

The static adapter **refuses to start** — the application does not serve at all — on any of:

| # | Condition | Why it is fatal |
| --- | --- | --- |
| FC-1 | Malformed JSON, or schema validation failure against the governed schema | The dataset is not the governed dataset |
| FC-2 | An unsupported or unknown field (`additionalProperties: false`) | Something was added outside governance |
| FC-3 | A non-null price **without** verified provenance | An unverified price could reach a page (FR-034, CI-5) |
| FC-4 | Missing provenance on any product — `source_record_id`, `source_document`, `source_document_sha256`, `source_page_pdf`, or `identity_grounding` | A displayed fact could not be traced to a checksummed source |
| FC-5 | Checksum mismatch on any of the three registers, or on a verified-price manifest if present | The file is not the file that was governed |
| FC-6 | A referenced media asset that is missing, or not `publication_status: approved_curated_launch_public`, or not `rights_status: human_authorized_selected_launch_use` | A disallowed asset could be published |
| FC-7 | A `source_record_id` that does not resolve in the source register | Specification values would be silently absent |
| FC-8 | A non-null value in any fabricated-claim field — `discount`, `stock`, `warranty`, `delivery_time`, `installation_sla`, `compatibility`, `market_country`, `tax`, `shipping`, `urgency_claim`, `popularity_claim` — or a non-empty `certifications` / `payment_methods` | A fabricated claim could reach a page (CI-6, CI-7) |
| FC-9 | Duplicate or unstable slug across products, categories, or collections | Routing identity would be ambiguous |

**Startup failures are deliberate.** Serving content that cannot be verified is worse than not
serving. A fail-closed boot is loud, immediate, and impossible to miss; a silently degraded page is
none of those things.

## The three governed source registers

The provider is fed by exactly three digest-pinned registers, copied read-only out of the legacy
repository. Their roles do not overlap, and **all three are required** — the catalogue alone yields
products with no images and no specifications.

| Register | Role | Key | Provenance carried |
| --- | --- | --- | --- |
| `curated-launch-catalog.v2.json` | **Identity, taxonomy, and publication authority.** 21 products; display name, summary, product type, supplier brand and relationship, category, collections, use cases, homepage role, media *pointers*, specification-field *allowlist*, commerce mode, permitted public actions, and the all-null commercial fields | `launch_id` / `source_record_id` | `source_document`, `source_document_sha256`, `source_page_pdf`, `identity_grounding`, `launch_publication_status`, `human_decision_id` |
| `product-media-register.v2.json` | **Media definitions.** 49 assets, 25 approved for launch; `original_path`, `original_name`, `sha256`, `file_size_bytes`, `format`, `mime_type`, `dimensions`, `alpha`, `mapping_status`, `match_confidence` | `asset_id` (`media-\d{3}`) | `sha256`, `rights_status`, `publication_status`, `candidate_model_mappings`, `source_page_mappings` |
| `product-source-register.v1.json` | **Specification values.** 209 source records; supplies the values for the five allowlisted fields as `{raw_value, normalized_value, source_page_pdf}` | `record_id` = catalogue `source_record_id` | per-value `source_page_pdf` page citation |

**Only allowlisted fields are read from the source register.** It also carries dimensions, weight,
battery, mortise, operating temperature, printed certifications, supplier legal name, and
`source_price_*` values — **none of which is on the allowlist and none of which may be published**
(FR-035). The loader reads allowlisted keys only, so an unlisted field cannot reach a template even
by accident.

**The legacy repository is never read at runtime and is never modified.** The registers are copied
in once, digest-pinned, and thereafter this repository is self-contained.

## Enforcement

1. **Contract test suite** — one suite runs against *every* adapter. `StaticCatalogProvider` passes
   it in Feature 001; `DatabaseCatalogProvider` must pass the identical suite before Feature 002
   can swap providers. This is the migration's definition of done.
2. **Boundary audit** — an automated check fails the build if `catalog/data/`, the loader module, or
   any provider-internal symbol is referenced from `templates/`, `static/src/js/`, or a context
   processor.
3. **Fake provider** — view, template, and form tests bind an in-memory fake with three fixed
   products, proving views depend on the port and not on the dataset.

## Feature 002 migration path

Feature 002 implements `DatabaseCatalogProvider` against Django models, runs the same contract
suite, flips `ZAKEY_CATALOG_PROVIDER`, and deletes the static adapter and its data file. Adding
verified prices then makes `Totals.computable` true and activates the existing price surfaces with
no template change — the price-on-request path and the priced path are already both implemented and
tested.
