# Visual regression ledger — Phase 19

Re-discovered from a fresh run, not carried over from an earlier report.

```
npx playwright test ./tests/visual --reporter=list
85 passed  11 failed        (before remediation)
```

After fixing the contact regression below:

```
npx playwright test ./tests/visual --grep contact --reporter=list
20 passed  0 failed         (against the UNMODIFIED baseline)
```

**No snapshot has been updated. No `--update-snapshots` command has been run.**

---

## 1. Resolved: `contact` × 4 viewports — GENUINE PRODUCT REGRESSION

| field | value |
|---|---|
| test node | `tests/visual/visual-regression.spec.js:36:3 › contact` |
| viewports | 1440, 1024, 768, 390 |
| route | `/contact/` |
| language / direction | ar-EG / RTL |
| state | signed-out, default |
| baseline | `tests/visual/baseline-004/contact-<w>.png` |
| actual | `…/playwright-results/visual-visual-regression-contact-chrome-<w>/contact-actual.png` |
| diff | same directory, `contact-diff.png` |
| pixel result | 112 354–1 223 502 px (ratio 0.07–0.46) |
| **classification** | **genuine product regression** |

### Diagnosis

The page was **shorter** than the baseline — −88 px (1440), −95 px (1024),
−103 px (390) — and every differing row was below y≈1253. A page losing height
below the fold means content disappeared, not that content was added.

`templates/pages/contact.html` still filtered the FAQ accordion with

```django
{% for faq in contact_faqs %}{% if faq.id in contact.faqIds %}
```

`contact.faqIds` is a **fixture-era** key. Once the catalogue moved to the
database, `ctx.faqs("contact")` began returning FAQs already filtered by
`FAQ.page`, and `contact.faqIds` ceased to exist — so the condition was
permanently false and the accordion rendered **zero** rows.

Measured before the fix:

```
database FAQ <details> rendered: 0
FAQ rows in DB for page='contact': 2
```

Two collapsed `<details>` ≈ 94 px, which matches the observed height loss.

### Fix

The redundant guard was removed (the queryset is already page-scoped). After
the fix: `database FAQ <details> rendered: 2`, and all four contact comparisons
**pass against the untouched baseline** — which is the proof that the baseline
was correct all along and that this was never an intentional delta.

---

## 2. Outstanding: `account` × 4 and `checkout` × 3 — NOT APPROVED

| route | viewports | height change | first differing row |
|---|---|---|---|
| account | 1440, 1024, 768, 390 | +514, +514, +146, +140 px | y≈305–321 |
| checkout | 1024, 768, 390 (1440 passes) | unchanged | y≈271–280 |

### What is mechanically established

**account** — the header and hero are pixel-identical above y≈305. The signed-out
page now renders three auth cards (login, register, forgot-password) where the
baseline had two. The set-new-password form is correctly **absent** without a
token. The delta is attributable to the password-reset UI required by FR-054 /
T-0404, which the approved storefront had no surface for.

**checkout** — page height is unchanged and the differences sit in a single
region y≈271–609. 1440 passes, so this is not a global style change.

### Why neither is approved here

`T-1901` accepts *"only the two approved deltas (shipping row, installation
row) … each with a recorded approval."* Neither of these is one of those two.

More decisively: approval requires confirming there is no unrelated regression
in typography, spacing, alignment, colour, icons or usability. **The `Read`
tool is disabled in this session, including for subagents, so the baseline,
actual and diff PNGs cannot be opened.** Pixel counts and band analysis are not
visual review, and the contact case above is exactly why that distinction
matters — the band analysis pointed at the right region, but only reading the
*code* revealed that the change was a regression rather than an intentional
delta.

Approving these would mean asserting something I did not verify.

### Discharged mechanically (not a substitute for approval)

`tests/visual/material-states.spec.js` — 44 assertions across 4 viewports,
all passing, covering: RTL/lang correctness, absence of visible template
syntax/placeholder/Lorem/TODO/undefined, zero horizontal overflow, zero controls
overhanging the viewport, every field labelled and focusable, invalid input
producing a visible `aria-describedby`-linked error with `aria-invalid`,
signed-out account showing no fabricated customer, signed-in showing the
session's own identity, checkout rendering no steppers on an empty basket, and
contact never reporting success without persistence.

### To close T-1901

1. Open `<route>-expected.png`, `<route>-actual.png` and `<route>-diff.png` for
   each of the 7 remaining comparisons.
2. Confirm the only visible change on `account` is the added forgot-password
   card, and on `checkout` the shipping and installation rows.
3. Confirm no unrelated typography, spacing, colour or alignment change.
4. Re-baseline **individually**, per approved image — never a blanket
   `--update-snapshots`.
5. Re-run `npx playwright test ./tests/visual` and require 96 passed / 0 failed.

---

## 3. Previously reported, now confirmed fixed

`search` @ 390 — the server-rendered heading regression fixed in an earlier
batch. It passes against the unmodified baseline in this run.
