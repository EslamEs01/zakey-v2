<!--
SYNC IMPACT REPORT
==================
Version change: 1.1.0 → 2.0.0
Amendment date: 2026-08-01
Ratification date (unchanged): 2026-07-31

Bump rationale (1.1.0 → 2.0.0, MAJOR): This amendment redefines existing principles in ways
that invalidate prior compliance, which the Versioning Policy classifies as MAJOR. Specifically:

  1. Principle XVI was vendor-exclusive ("Claude Code Governance") and named one assistant as
     the permanent project owner. It is redefined as capability-based ownership. Work that was
     compliant under the old rule solely because Claude Code performed it is no longer
     compliant on that basis alone; ownership now attaches to a named capability tier and a
     documented delegation brief.
  2. The ratified typography token changed from "Poppins, self-hosted" to "Cairo, self-hosted"
     as the primary typeface, with Poppins demoted to Latin-content use only. Principle II.1
     declared the ratified token set unalterable without amendment; this is that amendment, and
     any interface built to the previous token is now non-compliant.
  3. Principle IV.9 required only *future* localization and RTL readiness and explicitly stated
     that a language selector "is not approved". Arabic (`ar-EG`) and RTL are now the primary
     and only approved customer locale and direction. An LTR-first implementation that was
     compliant under v1.1.0 is now a violation.
  4. The Approved Stack deferred PostgreSQL until "persistent production data is introduced".
     PostgreSQL-compatible architecture is now binding from the outset.

Modified principles:
  I     Reference-Led Visual Fidelity — now subordinate to the Principle XIX grounding gate;
        prior-grounding observations demoted to a re-verification register (I.5, I.8, I.9).
  II    Permanent ZAKEY Brand System — typography token replaced; logical-CSS and
        direction-aware component rules added; focus-state and light-mode rules added
        (II.8-II.10).
  III   Approved Technical Foundation — Python 3.12, Django 5.2 LTS, PostgreSQL-compatible
        architecture, native ES modules, progressive enhancement, and the expanded prohibition
        list are now explicit (III.1-III.7).
  IV    Clean-Room Architecture — IV.9 redefined from "future RTL readiness" to "Arabic-first,
        RTL-primary"; clean-room boundary restated against the rejected v1 frontend and against
        the removed Specification 001 artifacts (IV.10).
  V     Content and Asset Integrity — provenance, data-driven credibility sections, and
        demonstration-fixture isolation rules added (V.2, V.4, V.9-V.11).
  VI    Functional Completeness — decimal-safe centralized money calculation made explicit;
        honest-unavailable state added (VI.11-VI.12).
  VII   Responsive Design — responsive work forbidden as a final CSS patch; zero unintended
        horizontal overflow made mandatory and programmatically verified (VII.2, VII.4, VII.6).
  VIII  Accessibility — focus trapping and return, RTL reading and focus order, and the
        no-critical-or-serious-violation acceptance bar added (VIII.5, VIII.6, VIII.9).
  X     Security, Privacy, and Data Safety — unsafe-redirect, file-validation, fixture and
        screenshot personal-data, and lead-review rules added (X.6, X.11-X.13).
  XI    Specification-First Development — lifecycle replaced by the fifteen ordered stage gates
        of the Development Workflow section; tasks.md is not implementation authority
        (XI.1, XI.10, XI.11).
  XII   Test-First Acceptance — verification set expanded with Ruff, Prettier, production
        Tailwind build, RTL verification, all-visible-control verification, and guard skills;
        tests must validate behavior and must not be weakened (XII.2-XII.4, XII.6).
  XIII  Visual QA and Consistency — bound to Principle XIX evidence (XIII.8).
  XV    Git and Repository Safety — allowed/prohibited action lists made explicit, including
        automatic commit hooks, deployment, server changes, destructive Git operations, and the
        stop-and-report rule for unsafe overlapping edits (XV.2, XV.3, XV.7-XV.10).
  XVI   Claude Code Governance → **Lead-Agent Governance and Delegation** (redefined,
        capability-based, vendor-neutral).
  XVII  LeanCtx → **LeanCTX and Context Discipline** — corrected capitalization; added that
        LeanCTX changes no Git or authorization boundary (XVII.7).
  XVIII Definition of Done — expanded from fifteen to twenty conditions.

Added principles:
  XIX   Targeted Visual Grounding Gate
  XX    Arabic-First Egyptian Market Experience
  XXI   Commerce, Payment, and Integration Honesty

Added sections:
  - Canonical Project Facts → "Feature and History Register" (feature 002 identity, the
    rejected-design decision, and the read-only status of removed Specification 001 artifacts).
  - Canonical Project Facts → "Reference Observations Pending Re-Verification".
  - Canonical Project Facts → "Ratified Egyptian Commerce Parameters".
  - Canonical Project Facts → "Approved Payment Presentation".
  - Development Workflow → "Stage Gates" (the fifteen ordered gates).
  - Governance → "Vendor Neutrality".

Removed sections: none. No principle was deleted; XVI was redefined in place.

Templates requiring updates:
  ✅ updated  .specify/templates/plan-template.md       (2026-08-01)
       Constitution Check tables extended from I-XVIII to I-XXI; the XVI row rewritten from
       "Claude governance" to capability-based lead-agent governance; the IV.9 row rewritten
       from "localization and RTL readiness" to Arabic-first RTL-primary; new rows for XIX
       (visual grounding evidence), XX (Egyptian market laws), and XXI (payment and integration
       honesty); the XVIII row updated from fifteen to twenty conditions; Technical Context
       defaults aligned to the ratified stack.
  ✅ updated  .specify/templates/spec-template.md       (2026-08-01)
       New mandatory §3 "Targeted Visual Grounding Evidence" (XIX) placed before Clarifications;
       new mandatory sections for Arabic-first / RTL / Egyptian market requirements (XX) and for
       payment and integration honesty (XXI); subsequent sections renumbered; Constitution
       Compliance now spans I-XXI.
  ✅ updated  .specify/templates/tasks-template.md      (2026-08-01)
       Phase V gains Ruff, Prettier, production Tailwind build, RTL and Arabic verification,
       all-visible-control verification, Egyptian-commerce calculation tests, and
       integration-honesty verification; the Definition-of-Done gate updated from fifteen to
       twenty conditions; a Phase 0 grounding precondition added.
  ✅ updated  .specify/templates/checklist-template.md  (2026-08-01)
       Definition-of-Done block expanded from DOD01-DOD15 to DOD01-DOD20.
  ➖ unchanged .specify/templates/constitution-template.md
       Upstream Spec Kit scaffold containing only placeholder slots. It is the source for a
       *new* constitution, inherits no governance content from this one, and needs no edit.

Deferred items / TODOs:
  ⚠ TODO(FEATURE_POINTER_STALE): `.specify/feature.json` still points at
    `specs/001-premium-storefront-experience`, a directory removed from the working tree in
    commit 05a37d0. Repointing it would create feature-002 Spec Kit state, which the governance
    scope of this amendment forbids. It is recorded here and MUST be resolved by the tooling at
    the Specification gate, not by hand during a governance-only change.
  ⚠ TODO(AUTO_COMMIT_HOOKS): `.specify/extensions.yml` sets `auto_execute_hooks: true` and
    registers `speckit.git.commit` on every `after_*` hook, plus a mandatory
    (`optional: false`) `speckit.git.initialize` on `before_constitution`. This conflicts with
    Principle XV.9, which forbids automatic commit hooks without an explicit user request. No
    hook was executed during this amendment. Disabling them is a tooling-configuration change
    outside this amendment's scope and requires the user's decision.

Prior entries (condensed):
  1.0.1 → 1.1.0 (MINOR, 2026-07-31): ratified colour table expanded from five to eighteen
    values after extraction of every designer-chosen colour literal in the approved reference;
    provenance rule, gradient rule, and the `#9CA3AF` non-text defect note added.
  1.0.0 → 1.0.1 (PATCH, 2026-07-31): closed TODO(LEGACY_REPO_PATH_CONFIRMATION); the verified
    legacy repository is `/media/mekky/work/backend/zakey.v1` (HEAD 5fdd81d), confirmed by the
    user as the authoritative initial product-content source.
  (uninitialized template) → 1.0.0 (2026-07-31): initial ratified adoption, Principles I-XVIII.
-->

# ZAKEY v2 Premium Egyptian Storefront Constitution

This constitution governs the clean-room rebuild of the ZAKEY e-commerce platform in the
repository `/media/mekky/work/backend/zakey-v2`. It binds the public storefront and every
future backend, admin, commerce, integration, deployment, and maintenance specification
produced for this platform.

Requirement keywords — MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY, OPTIONAL — are to be interpreted as described in RFC 2119. A rule stated
with MUST or MUST NOT is non-negotiable and cannot be waived by convenience, schedule
pressure, or an implementer's preference; it may be set aside only through the exception
procedure in **Governance**.

Every rule below is intended to be objectively checkable. Where a rule could be read as
subjective, the stated verification method decides compliance.

## Core Principles

### I. Reference-Led Visual Fidelity

The reference site recorded in **Canonical Project Facts** is the primary visual authority
for the public storefront.

1. Every UI implementation MUST preserve the reference's premium design direction, visual
   hierarchy, page composition, section order, proportions, spacing rhythm, typography
   character, component anatomy, product presentation, responsive behavior, and restrained
   luxury appearance.
2. Small creative improvements MAY be introduced, and only when they demonstrably improve
   usability, accessibility, responsiveness, product relevance, interaction clarity, or
   visual refinement. Each such improvement MUST be recorded in the owning specification with
   the improvement claimed and the reason for it.
3. Creative improvements MUST NOT transform the storefront into a different visual
   identity. A change that alters the brand palette, the typographic character, the layout
   density, or the overall design language is an identity change, not an improvement, and
   requires a constitutional amendment.
4. Visible reference defects MUST NOT be reproduced merely to achieve pixel similarity. A
   reference defect MAY be corrected only where the correction is required for usability,
   accessibility, RTL correctness, responsiveness, content truth, or an Egyptian-market
   requirement. The specification MUST state the defect, the correction, and the
   justification.
5. Fidelity claims MUST rest on evidence gathered under Principle XIX. A claim about what the
   reference contains is admissible only when it cites grounding evidence for the specific
   page or state at the specific width.
6. Every UI specification MUST define how reference fidelity will be inspected and verified,
   naming the pages compared, the widths compared at, and the acceptance threshold used.
7. Every page MUST belong to one coherent ZAKEY design system. Page-specific visual
   identities are forbidden.
8. Reference observations recorded before this amendment are advisory only until re-confirmed
   under Principle XIX. They are listed in the re-verification register in **Canonical Project
   Facts** and MUST NOT be cited as grounding evidence until re-confirmed.
9. Code generated by the reference's publishing runtime MUST NOT be copied, adapted, or used
   as the application architecture. The reference is authority over appearance and behavior,
   never over implementation.

*Rationale:* The reference encodes an approved premium direction that the project is not
free to reinvent page by page. Fidelity is the default; deviation is a documented decision.
Rule 8 exists because the prior storefront built on those observations was rejected by the
client, so no observation carries forward unexamined.

### II. Permanent ZAKEY Brand System

1. The approved visual foundation is the token set recorded in **Canonical Project Facts**.
   Those values are the ratified brand system and MUST NOT be altered without a
   constitutional amendment.
2. All design tokens MUST have exactly one centralized implementation source of truth — for
   example, a single tokens module consumed by the Tailwind configuration and by any
   template or script needing a token value. The implemented values MUST match the ratified
   table exactly.
3. Templates, components, and scripts MUST NOT invent competing colors, font scales,
   spacing values, radii, shadows, breakpoints, or interaction styles. Any value not
   derivable from the token source is a violation.
4. The interface MUST read as premium, modern, minimal, elegant, luxurious, technical, and
   trustworthy without visual excess. Compliance is decided at the visual critique passes
   required by Principle XIII, not by the implementer's self-assessment.
5. The project MUST NOT introduce, absent a constitutional amendment: dark mode; black or
   near-black full-bleed sections that read as an accidental dark theme; generic
   AI-generated styling; excessive gradients; excessive glassmorphism; random decorative
   elements; inconsistent colors; arbitrary spacing; oversized empty areas; repetitive
   generic promotional sections; distracting or excessive animation; mismatched components;
   or page-specific visual identities.
6. Spacing MUST be expressed in multiples of the 8px base unit. A value that is not a
   multiple of the base unit MUST be justified in the owning specification as a deliberate
   optical correction.
7. Accent gold MUST NOT be used as the color of text, of icons that convey meaning, or of
   any element that must satisfy a non-text contrast requirement, when placed on `#FFFFFF`
   or `#F8F9FB`. Measured contrast of accent gold on those backgrounds is approximately
   2.4:1, failing both the 4.5:1 text threshold and the 3:1 non-text threshold of Principle
   VIII. Accent gold on primary navy measures approximately 6.9:1 and is compliant. Gold MAY
   be used on light backgrounds for purely decorative elements that carry no information and
   whose absence would not change meaning.
8. Layout, spacing, alignment, and flow MUST be expressed with logical CSS properties —
   inline/block start and end — rather than physical left/right properties, except where a
   physical property is genuinely direction-independent. Components MUST be direction-aware
   by construction, not by an RTL override stylesheet.
9. Every interactive element MUST have a visible, accessible focus state meeting the contrast
   requirement of Principle VIII.3. Removing a focus outline without providing a compliant
   replacement is a violation.
10. Light mode is the default and only approved customer theme. No surface, section, or
    component may render as dark-themed.

*Rationale:* A single ratified token set is what makes twenty pages look like one product.
Rule 7 exists because the brand palette and the accessibility target would otherwise
silently conflict; the conflict is resolved once, here, rather than page by page. Rule 8
exists because an RTL-primary product built on physical properties accumulates a permanent
override tax.

### III. Approved Technical Foundation

1. The approved stack is the list recorded in **Canonical Project Facts**. Adopting any
   technology outside that list requires a constitutional amendment.
2. The project MUST NOT use, absent an approved amendment: React, Vue, Angular, Bootstrap,
   jQuery, the Tailwind CDN build, font CDNs, icon CDNs, code copied from a Figma or
   design-tool runtime export, or large UI libraries that would replace the ZAKEY design
   system.
3. Production assets MUST be compiled locally. A production page MUST NOT depend on a
   runtime CDN for CSS, JavaScript, fonts, or icons. Verification: no third-party origin
   appears in a network trace of a production-mode page load, and no `<link>` or `<script>`
   element in a rendered template points at a third-party origin.
4. Every new dependency MUST have a documented purpose and MUST be assessed, in the owning
   plan, for maintenance cost, security exposure, runtime performance, and bundle-size
   impact. A dependency added without that record MUST be removed or retroactively
   documented before acceptance.
5. Fonts MUST be self-hosted from files stored in the repository or produced by the build.
   Icons MUST be locally served Lucide assets or project-owned SVG.
6. Client behavior MUST follow progressive enhancement. Core navigation, catalog browsing,
   content, and form submission MUST function server-side; JavaScript enhances these paths
   and MUST NOT be the only way to complete a core journey.
7. JavaScript MUST be authored as native ES modules. A bundler or transpiler that introduces
   a framework runtime is prohibited under rule 2.

*Rationale:* The stack is deliberately small and locally compiled so the storefront stays
fast, auditable, and free of third-party runtime dependencies ZAKEY does not control.

### IV. Clean-Room Architecture

1. The legacy project's frontend implementation, templates, page structure, CSS
   architecture, JavaScript architecture, and design system MUST NOT be copied into this
   repository. Large inherited CSS files MUST NOT be imported in whole or in part.
2. The legacy repository MUST remain strictly read-only. No process, agent, script, or
   command run for this project may create, modify, move, or delete any file inside it.
   Inspection MUST use read-only operations. Copying an approved asset out of the legacy
   repository is permitted under Principle V and does not modify it.
3. The new implementation MUST use reusable Django templates and partials, centralized
   design tokens, structured context data, reusable UI components, isolated page-specific
   behavior, clearly separated frontend assets, and maintainable JavaScript modules.
4. Shared components MUST NOT be duplicated between pages. Where two pages need the same
   element, they MUST include the same partial or component.
5. Reusable implementations MUST exist for every applicable element, including announcement
   bars, headers, mobile navigation, breadcrumbs, section headings, product cards, prices,
   ratings, badges, buttons, form fields, filters, pagination, drawers, dialogs, empty
   states, toast notifications, newsletters, and footers.
6. A single oversized CSS or JavaScript file MUST NOT become the project architecture.
   JavaScript MUST be organized as focused modules with explicit responsibilities.
7. Temporary storefront data MUST be isolated behind exactly one documented fixture,
   service, repository, or data adapter, so it can later be replaced by database-backed
   content without touching templates.
8. Templates MUST NOT independently hardcode copies of the same product, collection,
   category, or business record.
9. The architecture MUST be Arabic-first and RTL-primary by construction, per Principle XX —
   externalized strings, direction-aware layout primitives, logical CSS properties, and no
   layout that assumes LTR-only geometry. A customer-facing language selector is not approved
   and MUST NOT be introduced without an amendment.
10. The rejected v1 storefront design and the Specification 001 artifacts removed from the
    working tree MUST NOT be restored into it. They exist in Git history as advisory evidence
    only and MAY be inspected with read-only Git commands.

*Rationale:* This is a rebuild, not a port. The value of starting over is lost if legacy
structure is carried across, and lost again if the new structure decays into per-page
duplication.

### V. Content and Asset Integrity

1. All visible content MUST be truthful, relevant, and appropriate for ZAKEY smart locks and
   smart-home products.
2. Verified content and assets from the legacy repository SHOULD be reused where available,
   copied out under the read-only constraint of Principle IV. Every production asset and
   every material business claim — logos, product media, product information, categories, and
   business data — MUST carry documented provenance.
3. The project MUST NOT invent awards, certifications, partnerships, integrations, customer
   numbers, sales totals, review counts, customer reviews, ratings, technical
   specifications, warranties, stock levels, delivery promises, media coverage, trust badges,
   or business addresses.
4. Any claim that cannot be traced to a verified source MUST be removed, hidden, or replaced
   with conservative, product-focused wording. Unverified production content MUST be hidden
   rather than fabricated.
5. Visible production interfaces MUST NOT contain the words "demo", "placeholder", "Figma",
   "Jazzmin", internal notes, or any other development terminology — in copy, alt text,
   titles, ARIA labels, user-visible filenames, or metadata.
6. Placeholder images MUST NOT remain in an accepted release.
7. Product images MUST preserve their source aspect ratio and quality, and MUST NOT appear
   stretched, damaged, incorrectly cropped, or visibly degraded.
8. Asset sources, ownership, and licensing assumptions MUST be documented in the owning
   specification or in a dedicated asset manifest.
9. Reviews, testimonials, partner sections, ratings, and similar credibility surfaces MUST be
   data-driven. Where the underlying data is absent or unverified, the section MUST NOT
   render at all.
10. Development demonstration fixtures MUST be stored, named, and loaded separately from
    production content, and MUST be identifiable as demonstration data at the data layer.
11. It MUST NOT be possible to publish demonstration data as verified production content by
    accident. The separation MUST be enforced by configuration or by an explicit guard, not by
    convention, and MUST be covered by a test.

*Rationale:* A storefront that invents credibility signals is both a legal exposure and a
trust failure. Conservative truthful copy is always acceptable; fabricated proof never is.

### VI. Functional Completeness

1. Every visible control MUST have intentional behavior — buttons, links, icons, inputs,
   tabs, menus, filters, selectors, drawers, dialogs, carousel controls, quantity controls,
   forms, and commerce actions.
2. Dead controls are forbidden. A control that renders but does nothing MUST either be
   implemented or removed.
3. `href="#"` is forbidden in a finished interface. Decorative elements MUST NOT be presented
   as interactive.
4. Fake success states are forbidden. A success message MUST NOT be shown unless the
   underlying operation actually succeeded.
5. Internal navigation MUST use valid named Django URLs resolved through `{% url %}` or an
   equivalent reverse lookup. Hardcoded internal paths are forbidden.
6. Forms MUST provide server-side validation, appropriate client-side assistance, loading
   states where applicable, clear validation errors, success states, and failure states.
7. Loading, empty, unavailable, disabled, error, and success states MUST be intentionally
   designed wherever they are reachable.
8. Commerce prices, totals, taxes, discounts, and shipping charges MUST originate from
   authoritative data and MUST be calculated by one shared, tested routine. Two surfaces MUST
   NOT compute the same total differently.
9. Frontend payment simulations MUST NOT request, collect, transmit, log, or persist real
   card details.
10. Future real payments MUST be handled by a compliant payment gateway. ZAKEY MUST NEVER
    store prohibited payment credentials, including full card numbers, CVV/CVC values, PINs,
    or magnetic-stripe data.
11. Monetary values MUST be represented and computed with a decimal type. Binary floating
    point MUST NOT be used for money, and rounding MUST be explicit and centralized.
12. Every visible interaction MUST either work as intended or be visibly and honestly
    presented as unavailable. Inert frontend behavior presented as working is a violation.

*Rationale:* A storefront is judged by whether things work when clicked. Half-wired UI is
worse than absent UI, because it teaches customers the site is unreliable.

### VII. Responsive Design

1. Every public page and every reusable component MUST be intentionally designed and
   verified at the four widths recorded in **Canonical Project Facts**: 1440px desktop,
   1024px tablet, 768px transition, 390px mobile.
2. Responsive implementation MUST NOT consist only of stacking desktop columns, and MUST NOT
   be treated as a final CSS patch applied after the desktop layout is complete. Each width
   MUST receive a deliberate layout decision made during specification.
3. An accepted interface MUST exhibit none of the following at any of the four widths:
   horizontal overflow, clipped content, header collisions, overlapping floating elements,
   tablet dead zones, inaccessible navigation, unreadable product cards, unstable image
   sizing, oversized empty sections, unusable mobile forms, or unusable mobile checkout.
4. Zero unintended horizontal overflow is mandatory and MUST be verified programmatically, by
   asserting that the document scroll width does not exceed the viewport width at each of the
   four widths.
5. Mobile navigation, filters, galleries, tables, drawers, dialogs, and checkout actions MUST
   each receive dedicated responsive behavior, specified before implementation.
6. Every affected page MUST be captured and visually inspected at all four widths before
   acceptance, per Principles XIII and XIX.

*Rationale:* Most storefront traffic is not desktop. Tablet is where naive responsive work
fails first, which is why 1024px and 768px are both mandatory checkpoints.

### VIII. Accessibility

1. The project MUST target WCAG 2.2 Level AA as the acceptance baseline wherever applicable.
2. Implementations MUST provide semantic HTML, a correct heading hierarchy,
   keyboard-operable interactions, visible focus indicators, accessible names for icon-only
   controls, explicit form labels, programmatically connected validation errors, sufficient
   color contrast, usable touch targets, accessible dialogs and drawers, reduced-motion
   support, meaningful alternative text, and correct page language and direction attributes.
3. Text and images of text MUST meet a contrast ratio of at least 4.5:1, or 3:1 for large
   text as defined by WCAG. Meaningful non-text elements, including UI component boundaries
   and focus indicators, MUST meet at least 3:1.
4. Interactive targets MUST be at least 24×24 CSS pixels, and SHOULD be at least 44×44 CSS
   pixels for primary mobile commerce actions.
5. Dialogs and drawers MUST trap focus while open and MUST return focus to the invoking
   control when dismissed.
6. Reading and focus order MUST be correct in RTL for both sighted keyboard users and screen
   readers. A visually correct RTL layout with an incorrect underlying DOM order is a
   violation.
7. Accessibility MUST be verified by both automated axe checks and manual keyboard-focused
   inspection covering tab order, focus visibility, focus trapping in dialogs and drawers,
   and escape or dismiss behavior.
8. Automated accessibility checks alone are insufficient for final acceptance. A feature with
   a clean axe run and no manual keyboard pass is not accessibility-verified.
9. No feature may be accepted with an unresolved critical or serious accessibility violation.

*Rationale:* Automated tooling catches a minority of real barriers. The manual pass is what
distinguishes a page that passes a scanner from a page a keyboard user can actually buy
from.

### IX. Performance and Frontend Quality

1. Production pages MUST avoid unnecessary JavaScript and oversized dependencies.
2. Images MUST use suitable formats, dimensions, responsive variants, and loading strategies.
   Above-the-fold imagery SHOULD be eagerly loaded; below-the-fold imagery SHOULD be lazily
   loaded.
3. Intrinsic image dimensions or an equivalent aspect-ratio reservation MUST be declared so
   images do not cause avoidable layout shift.
4. Fonts MUST be served locally and loaded efficiently, with a font-display strategy that
   avoids invisible text.
5. Production CSS and JavaScript MUST be compiled and optimized by the local build.
6. An accepted page MUST NOT emit unexpected browser-console errors. Console output MUST be
   captured automatically during end-to-end verification, and the error count MUST be zero
   or each error individually justified in the specification.
7. Each relevant feature specification MUST define measurable performance budgets — at
   minimum a page-weight budget, a JavaScript-payload budget, and a layout-stability target —
   before implementation begins.
8. Performance optimization MUST NOT remove required accessibility, content, or usability
   behavior.

*Rationale:* Budgets set before implementation are engineering constraints; numbers measured
after implementation are only observations.

### X. Security, Privacy, and Data Safety

1. Secrets, credentials, API tokens, private keys, and production data MUST NOT be committed
   to the repository.
2. Sensitive configuration MUST be supplied through environment variables validated at
   startup, and the application MUST fail loudly when a required variable is missing or
   malformed.
3. Django's built-in security protections MUST NOT be bypassed or disabled.
4. CSRF protection MUST remain active for every state-changing request.
5. All user-provided data MUST be validated server-side. Client-side validation is
   assistance, never the enforcement boundary.
6. User-generated HTML or content MUST be escaped or sanitized appropriately. Autoescaping
   MUST NOT be disabled for untrusted content. Redirect targets MUST be validated against an
   allowlist; open redirects and injection vectors are forbidden.
7. Authentication, authorization, session handling, and administration MUST follow least
   privilege and secure-session practice.
8. Personal information MUST NOT be exposed to unauthorized users, including through URLs,
   enumerable identifiers, API responses, or error output.
9. Logs MUST NOT contain passwords, payment credentials, authentication secrets, session
   secrets, or unnecessary personal information.
10. Destructive operations MUST require explicit authorization, a suitable confirmation step,
    and appropriate auditability.
11. Uploaded files and media MUST be validated for type, size, and content before being
    stored or served.
12. Production personal data MUST NOT appear in fixtures, test data, screenshots, or any
    verification artifact.
13. Security-sensitive decisions MUST be owned by the lead capability tier under Principle
    XVI, MUST be reviewed before integration, and MUST carry appropriate tests.

*Rationale:* Commerce software holds other people's money and identities. These are the
minimum controls under which such software may be accepted.

### XI. Specification-First Development

1. Project work MUST follow the fifteen ordered stage gates defined in **Development Workflow
   and Quality Gates**. A stage MUST NOT be skipped where it applies; a stage that does not
   apply MUST be recorded as not applicable, with a reason.
2. A specification MUST define required outcomes and behaviors before implementation begins.
3. Material ambiguity MUST be resolved before planning. An ambiguity is material when two
   reasonable readings would produce materially different work.
4. Plans MUST demonstrate compliance with this constitution through an explicit per-principle
   constitution check covering Principles I-XXI.
5. Tasks MUST be traceable to specific requirements and acceptance criteria.
6. Cross-artifact analysis MUST identify missing requirements, contradictions, duplicated
   requirements, untestable acceptance criteria, missing edge cases, and constitutional
   violations.
7. Implementation MUST NOT silently redefine approved requirements.
8. A material scope change MUST first be reflected in the approved specification, plan, and
   tasks, and only then implemented.
9. Every specification MUST explicitly identify what is out of scope.
10. A later stage MUST NOT begin while a blocking inconsistency remains in an earlier stage.
    The existence of a `tasks.md` file is not authority to implement: cross-artifact analysis
    and the correction of every material finding MUST pass first.
11. Specification, plan, and tasks MUST remain traceable to one another and to the visual
    grounding evidence required by Principle XIX.

*Rationale:* Ambiguity resolved during implementation is resolved by whoever is typing,
without review. Resolving it in the specification is what makes review possible.

### XII. Test-First Acceptance

1. Every feature specification MUST define measurable acceptance criteria before
   implementation begins.
2. Verification MUST include the applicable combination of: Django system checks; Python
   tests; model tests; service tests; form tests; view tests; permission tests;
   template-rendering tests; JavaScript behavior tests; Playwright end-to-end journey tests;
   axe accessibility tests; manual keyboard verification; RTL verification; broken-link
   verification; all-visible-control verification; console-error checks; responsive-overflow
   checks; Ruff; Prettier checks; a production Tailwind build; screenshot capture and human
   visual inspection; reference comparison; two documented visual correction passes; and the
   `clean-code-guard`, `test-guard`, and `docs-guard` skills. The owning specification MUST
   state which of these apply and MUST justify each exclusion.
3. Tests MUST validate behavior, not merely implementation details.
4. Tests MUST NOT be weakened, narrowed, skipped, or rewritten to make an incorrect
   implementation pass.
5. Bug fixes SHOULD include a regression test whenever technically practical.
6. A feature MUST NOT be reported as complete when required tests were not run, required
   tests are failing, failures were hidden or ignored, results were estimated rather than
   observed, visual evidence was captured but not inspected, dead controls remain, fabricated
   data is presented as truth, a critical or serious accessibility violation is unresolved, or
   known limitations were omitted from the report.
7. "Implemented" and "verified" MUST be reported as two separate facts. Reporting an
   unverified implementation as complete is a constitutional violation.
8. Reported results MUST include the exact commands executed and their exact outcomes.
   Paraphrased or reconstructed results are forbidden.

*Rationale:* The most damaging failure mode in agent-driven development is a confident
completion report for unverified work. Rules 4-8 exist to make that failure impossible to
commit accidentally.

### XIII. Visual QA and Consistency

1. Every UI specification MUST include an inventory of pages, components, responsive states,
   empty states, error states, and interactions.
2. Screenshots MUST be captured at all four ratified verification widths.
3. Major storefront work MUST undergo at least two documented visual critique and correction
   passes after initial implementation.
4. Visual inspection MUST cover every affected page, not only the homepage.
5. Repeated components MUST be compared across pages for dimensions, spacing, colors,
   typography, focus states, responsive behavior, and interaction behavior. Divergence
   between two instances of the same component is a defect.
6. Capturing screenshots without inspecting them does not count as visual QA. The
   verification record MUST state what was observed in each inspected screenshot.
7. Any unapproved deviation from the reference design direction MUST be corrected, or
   truthfully documented and raised for a decision.
8. Visual QA MUST compare the implementation against the grounding evidence captured under
   Principle XIX for the same page, state, and width. A comparison against memory, a verbal
   description, or a different page is not a comparison.

*Rationale:* Screenshot files are not evidence; inspected screenshots are. Two critique
passes are required because the first reliably finds obvious defects and the second reliably
finds the consistency defects the first pass introduced.

### XIV. Code Quality

1. Code MUST be readable, maintainable, cohesive, and appropriately typed.
2. Names MUST describe business intent rather than mechanism.
3. Non-obvious behavior MUST be documented at the point of definition.
4. Copy-pasted business logic is forbidden. Shared behavior MUST live in one place.
5. Broad exception swallowing is forbidden. Caught exceptions MUST be narrow and handled
   deliberately.
6. Accepted work MUST NOT retain debug printing, temporary logging, commented-out
   implementations, abandoned experiments, unused code, or unexplained lint suppressions.
7. Tests and lint rules MUST NOT be bypassed through blanket ignores, skipped test
   directories, or configuration that disables a rule project-wide to silence one site.
8. Database changes MUST use reviewed Django migrations.
9. Data migrations MUST be deterministic, MUST be reversible where practical, and MUST
   preserve existing data safely.
10. The `clean-code-guard`, `test-guard`, and `docs-guard` skills MUST be run during final
    verification whenever their scopes apply, and their findings MUST be resolved or
    explicitly justified.

*Rationale:* Generated code accumulates residue — debug prints, dead branches, duplicated
logic — faster than hand-written code. These rules make removing that residue a gate rather
than an aspiration.

### XV. Git and Repository Safety

1. Every new feature specification MUST use a separate local branch following the Spec Kit
   numeric naming convention (`###-feature-name`).
2. The following are allowed without further authorization: read-only repository inspection;
   creation of the local feature branch explicitly required by the current task; local
   working-tree edits inside the approved scope; and local tests and builds.
3. The following are prohibited unless the user explicitly requests them in the current
   session: commits; pushes; pull requests; merges; remote changes of any kind; deleting
   branches; rewriting history; destructive resets; automatic commit hooks; production
   deployment; server changes; and external control-plane changes.
4. Existing user changes MUST be preserved. Uncommitted user work MUST NOT be discarded,
   stashed, reverted, or overwritten.
5. Unrelated files MUST NOT be modified or reformatted. A formatting pass MUST be confined to
   files the current task legitimately touches.
6. Secrets, databases, uploaded media, test recordings, temporary screenshots, dependency
   caches, and generated artifacts MUST be covered by the repository ignore policy and MUST
   NOT be committed.
7. Only the feature branch required by the current task may be created. Speculative or
   additional feature branches MUST NOT be created.
8. `git reset --hard`, destructive checkout operations that discard working-tree state, and
   broad recursive deletion commands MUST NOT be used.
9. Automatic commit hooks MUST NOT be executed. Where the tooling registers one, it MUST be
   declined and the decline MUST be reported.
10. If the working tree contains overlapping edits that make an authorized change unsafe,
    work MUST stop and the exact conflict MUST be reported rather than resolved unilaterally.
11. The final report of any session MUST truthfully list every Git action performed, and MUST
    state explicitly when none were performed.

*Rationale:* Version-control actions are the hardest to undo and the easiest to perform by
reflex. Authority for them stays with the user.

### XVI. Lead-Agent Governance and Delegation

This constitution is not bound to any commercial model, vendor, or assistant. Ownership
attaches to capability and to a named role, not to a product name.

1. **The active lead agent** owns requirements integrity, architecture, design-system
   coherence, integration review, risk decisions, visual review, and final verification. There
   is exactly one active lead at any time, and it MUST be named in the owning artifacts.
2. Claude Code is the active lead for the current Constitution, Specification, Plan, and Tasks
   preparation stages of this project.
3. Implementation MAY be performed by Claude Code or by Codex under this same constitution.
   Substituting the implementing agent changes nothing about the rules that bind it.
4. A **strong reasoning model** MUST retain ownership of: architecture; shared files;
   security-sensitive work; checkout and monetary calculations; global design tokens;
   integration; difficult debugging; and final acceptance. These MUST NOT be fully delegated
   to a bounded worker agent.
5. **Bounded worker agents** MAY handle isolated, clearly defined, non-overlapping work.
6. Every delegated task MUST state, in writing and before work begins: its exact scope; the
   files it is allowed to modify; the files it is forbidden to modify; the acceptance evidence
   it must return; and the tests it must run.
7. Two agents MUST NEVER modify the same shared files concurrently. Shared templates, design
   tokens, global CSS, shared JavaScript, migrations, and central configuration are
   single-writer surfaces.
8. The lead MUST review every delegated change before integration. Agent output is evidence,
   not automatic acceptance, and the lead remains responsible for its correctness,
   consistency, and completeness.
9. Agent speed, cost, availability, or context limitations NEVER justify weakening a
   requirement, reducing scope silently, lowering a test's strength, or skipping verification.
   Where a limitation genuinely blocks work, it MUST be reported as a blocker, not absorbed.
10. Where third-party assistants or review tools are used, their output is advisory evidence
    only; the active lead retains ownership and final responsibility.
11. Work MUST NOT stop merely because one delegated agent completed its assigned task. The
    lead MUST continue through the approved scope until all tasks are complete, integration is
    complete, tests have run, visual QA has run, failures have been corrected, and final
    verification has completed — unless a genuine blocker requires user authority or a material
    product decision.

*Rationale:* Delegation multiplies output and dilutes accountability unless ownership is
named. Naming a vendor instead of a capability makes the governance expire the moment the
tooling changes; naming the capability makes it durable.

### XVII. LeanCTX and Context Discipline

1. LeanCTX MUST be used throughout large project work when it is available.
2. Before major repository exploration, the active lead SHOULD verify the LeanCTX connection
   and status.
3. The lead and its agents MUST avoid repeatedly loading the same large files without a
   justified need. A targeted read MUST be preferred where it is sufficient.
4. Repository exploration SHOULD be targeted and evidence-driven rather than exhaustive.
5. Context compression MUST NOT be used as an excuse to lose approved requirements,
   architectural decisions, task status, test evidence, or known blockers.
6. Important decisions and verification evidence MUST be written into the appropriate Spec
   Kit artifacts rather than left only in conversation context.
7. LeanCTX changes no Git boundary and no authorization boundary. Principle XV applies to
   every LeanCTX-mediated command exactly as it applies to a direct one.

*Rationale:* Anything that exists only in a conversation is lost at the next compaction.
Durable artifacts are the project's memory.

### XVIII. Definition of Done

A specification is complete only when all twenty of the following hold:

1. All in-scope requirements are implemented.
2. Every requirement is traceable to an acceptance criterion.
3. All required tests pass.
4. All required manual checks are completed.
5. All required visual checks are completed.
6. All captured screenshots have been inspected, and the observations are recorded.
7. Responsive behavior is verified at all four approved widths, with zero unintended
   horizontal overflow.
8. Accessibility is verified by both automated and manual means, with no unresolved critical
   or serious violation.
9. Production assets build successfully, including the production Tailwind build.
10. No dead controls remain, and every visible control has been exercised.
11. No unexpected console errors remain.
12. Documentation is current.
13. Known limitations are truthfully recorded.
14. Unrelated user work remains untouched.
15. The final report includes the exact commands executed and their exact results.
16. Every implemented page and component cites the Principle XIX grounding evidence it was
    built and compared against.
17. Arabic-first and RTL correctness is verified, including document language and direction,
    reading order, focus order, and Egyptian-pound and number formatting.
18. Every visible business claim, asset, and price carries documented provenance, and nothing
    unverified is presented as a production fact.
19. Every external integration is either genuinely implemented and verified, or presented
    honestly as unavailable or integration-ready.
20. Two documented visual critique and correction passes have been completed for major
    storefront work.

Passing only a subset of the required conditions does not satisfy this Definition of Done.
Work that meets nineteen of these twenty conditions is not done.

*Rationale:* "Done" must be a checklist with a single interpretation, or it becomes a
judgment call made by whoever wants to stop working.

### XIX. Targeted Visual Grounding Gate

The published reference is the primary visual authority, and that authority is exercised only
through inspected evidence. Before any page, section, or component is specified or
implemented, the responsible lead MUST complete the following gate for that exact surface.

1. Inspect the exact corresponding reference page or state in a real browser. Inspecting a
   different page, recalling a previous session, or reasoning from a description does not
   satisfy this rule.
2. Inspect the relevant desktop, tablet, and mobile behavior of that surface, including its
   interactive states.
3. Capture or record evidence at 1440px, 1024px, 768px, and 390px.
4. Record, for the inspected surface: section order, component anatomy, container widths,
   grid behavior, typography, spacing, colors, radii, shadows, image ratios, states, and
   responsive transformations.
5. Map each planned page and component to the specific inspected reference evidence that
   grounds it.
6. Document any deviation from the reference and its justification.
7. Correct visible reference defects only where the correction is required for usability,
   accessibility, RTL correctness, responsiveness, content truth, or an Egyptian-market
   requirement. Every correction MUST be recorded with its reason.
8. Never copy the reference's generated runtime source code as the application architecture.
9. **No page, section, or component may be considered specified or implemented without its
   own targeted visual evidence.** Grounding is per surface; grounding one page does not
   ground another.
10. Grounding evidence MUST be recorded in the owning Spec Kit artifacts, with the date of
    inspection, so that a later reviewer can tell what was seen and when.
11. Small creative improvements are permitted only where they clearly improve usability,
    accessibility, responsiveness, product relevance, or visual refinement without changing
    the approved identity, and only when recorded under Principle I.2.

*Rationale:* The previous storefront was rejected despite being built against this same
reference. The failure mode was building from a general impression rather than from inspected
specifics. This gate makes the specific inspection a precondition rather than a habit.

### XX. Arabic-First Egyptian Market Experience

ZAKEY v2 is an Egyptian product. Arabic is not a translation layer applied to an English
product; it is the product.

1. The customer experience MUST be Arabic-first, using natural Arabic suitable for Egypt.
   Machine-literal copy that reads as translated is a defect.
2. The primary locale is `ar-EG` and the primary direction is RTL. Documents MUST declare
   `lang="ar"` and `dir="rtl"` at the document level.
3. Cairo, self-hosted, is the primary typeface. Poppins MAY be used only for Latin content
   where appropriate, and MUST NOT become the typeface of the Arabic interface.
4. Egyptian-pound formatting MUST be centralized in one implementation and MUST render the
   currency in the visible form `ج.م`. No template, script, or view may format currency
   independently.
5. Number formatting MUST be consistent across the entire storefront, decided once, and
   applied through the same centralized formatting layer.
6. Egyptian VAT is 14%. It MUST be applied through the shared, tested calculation routine
   required by Principle VI.8, and MUST NOT be duplicated as a literal across surfaces.
7. The free-shipping threshold is 1,500 EGP, applied through the same shared routine.
8. All monetary calculations MUST be centralized and decimal-safe, per Principle VI.11.
9. Product prices MUST be data-driven. Prices MUST NOT be hardcoded into templates.
10. Legacy product evidence MAY support an approximate range of 2,190-7,490 EGP. That range is
    advisory evidence about the catalog's shape, not a source of truth. An unverified price
    MUST NEVER be presented as a production fact.
11. All 27 Egyptian governorates MUST be supported wherever a governorate is selected or
    displayed.
12. Egyptian phone-number validation is REQUIRED, server-side, on every field that collects a
    phone number.
13. Address capture MUST include detailed address fields and a landmark field, consistent with
    Egyptian delivery practice.
14. Same-day delivery in Greater Cairo MUST be configuration-driven. It MUST NOT be hardcoded
    and MUST NOT be displayed where the configuration does not enable it.
15. Installation service in Greater Cairo and Alexandria MUST be configuration-driven, under
    the same constraint as rule 14.
16. The hotline `19919` and the New Cairo location MUST be centrally configurable and
    provenance-recorded. They MUST NOT be scattered as literals through templates.

*Rationale:* Every value in this principle is a business fact that would otherwise be
duplicated into a dozen templates and drift. Centralizing them once makes the storefront
correctable in one place when the business changes.

### XXI. Commerce, Payment, and Integration Honesty

1. Approved payment presentation MAY include: Cash on Delivery; Vodafone Cash; e& Cash /
   Etisalat Cash; CashU; InstaPay transfer; and Egyptian bank-card installment presentation
   for 6 and 12 months.
2. Raw card information MUST NEVER be stored, in any form, at any layer.
3. Completed payments MUST NEVER be simulated. A payment success state MUST NOT be rendered
   unless a real, verified transaction succeeded.
4. An external integration MUST NOT be presented as active without verified credentials and a
   real implementation behind it.
5. Gateway credentials MUST NOT be hard-coded. They MUST be supplied through validated
   environment configuration, per Principle X.2.
6. Shipping providers and brands MUST NOT be presented as official partners without verified
   authorization.
7. External payment and delivery providers MUST be reached through configuration-driven
   adapter boundaries. Provider-specific logic MUST NOT leak into views, templates, or the
   shared calculation routine.
8. An unimplemented integration MUST show an honest unavailable or integration-ready state.
   Silence, a dead control, or a plausible-looking non-functional flow are all violations.
9. Installment presentation MUST state its terms truthfully and MUST NOT imply an approved
   arrangement with a bank that has not been verified.

*Rationale:* Payment surfaces are where a dishonest interface stops being an aesthetic
problem and becomes a legal and financial one. An honest "not available yet" costs nothing;
a convincing fake costs the business its credibility.

## Canonical Project Facts

This section is the authoritative registry referenced by Principles I, II, III, IV, VII, XIX,
XX, and XXI. Changing any value here requires a constitutional amendment.

### Identity and Locations

| Fact | Value |
| --- | --- |
| Project name | ZAKEY v2 Premium Egyptian Storefront |
| Product | ZAKEY v2 — smart locks and smart-home products |
| Market | Egypt |
| Target repository (read-write) | `/media/mekky/work/backend/zakey-v2` |
| Remote repository | `https://github.com/EslamEs01/zakey-v2` |
| Legacy repository (STRICTLY READ-ONLY) | `/media/mekky/work/backend/zakey.v1` |
| Primary visual reference | `https://remote-fried-86528699.figma.site/` |
| Primary locale | `ar-EG` |
| Primary direction | RTL |
| Approved customer theme | Light mode only |
| Visual positioning | Premium, modern, minimal, elegant, luxurious, technical, trustworthy |

The legacy repository MAY be inspected only to obtain verified ZAKEY logos, brand assets,
product images, product information, categories, collections, and truthful business content,
each with documented provenance. It MUST NOT be modified in any way.
`/media/mekky/work/backend/zakey.v1` is the verified legacy ZAKEY Django project (HEAD
5fdd81d), confirmed by the user as the authoritative initial product-content source.

### Feature and History Register

| Fact | Value |
| --- | --- |
| Current feature identifier | `002-egypt-premium-storefront` |
| Current branch | `002-egypt-premium-storefront` |
| Superseded feature | `001-premium-storefront-experience` |

The storefront design produced under Specification 001 was rejected by the client. Its
application code and specification artifacts were removed from the working tree in commit
`05a37d0`. Those artifacts MUST NOT be restored into the working tree. They remain in Git
history and MAY be inspected with read-only Git commands as advisory evidence only; nothing
found in them overrides this constitution or the current reference.

ZAKEY v2 is a clean-room frontend rebuild. The v1 frontend architecture, templates, page
structure, and large CSS files MUST NOT be reused (Principle IV.1).

### Ratified Design Tokens

This is the complete ratified ZAKEY colour system, expanded to eighteen values in v1.1.0 after
every designer-chosen colour literal in the approved reference was extracted and classified.
**Core brand tokens** carry the brand identity; **reference-derived support tokens** are equally
binding parts of the approved visual system, not optional suggestions. No colour outside this
table may appear in an accepted interface, and every value here MUST be implemented through one
centralized token source (Principle II.2).

Provenance rule: the designed palette is every colour the reference author chose explicitly —
that is, every arbitrary-value colour literal in the published reference. Colours inherited from
framework defaults (unprefixed utility classes) are **not** part of the ratified system, except
`#FFFFFF`, which is unambiguous and independently ratified. A colour whose only observed use is
in content this project removes as fabricated, or defers to a later feature, is not ratified.

Re-verification rule (added in v2.0.0): these values remain binding and MUST NOT be altered
unilaterally. The Principle XIX grounding gate re-confirms each token's observable role per page
and per state as surfaces are specified. If grounding shows a ratified value is absent, misused,
or wrong, that is a defect report requiring an amendment — never a unilateral substitution.

#### Core brand tokens

| Token | Value | Observable reference role | Permitted semantic uses | Contrast limitation |
| --- | --- | --- | --- | --- |
| Primary navy | `#0D1B3D` | text, backgrounds, borders, gradient stops (173 uses) | body and heading text on light surfaces, full-bleed section backgrounds, borders, gradient stops | 16.92:1 on white, 16.06:1 on `#F8F9FB` — passes everywhere |
| Accent gold | `#C9A227` | text, backgrounds, borders, icon fills, form accent (136 uses) | decorative accents, borders, icon fills on compliant surfaces, backgrounds with compliant foreground, form control accent, large text only where measured compliant | **2.42:1 on white and 2.30:1 on `#F8F9FB` — MUST NOT be normal-sized text on either.** 6.99:1 on primary navy — compliant there |
| Main background | `#F8F9FB` | page background (55 uses) | page and section backgrounds | background role only |
| White | `#FFFFFF` | text, backgrounds, borders, placeholder (117 uses via named utility) | surfaces, cards, text on navy, borders on navy | 16.92:1 against primary navy |
| Primary text | `#1F2937` | text (22 uses) | body text on light surfaces | 14.68:1 on white, 13.93:1 on `#F8F9FB` |

#### Reference-derived support tokens

| Token | Value | Observable reference role | Permitted semantic uses | Contrast limitation |
| --- | --- | --- | --- | --- |
| Secondary text | `#6B7280` | text (63), placeholder (1) | secondary and muted text, placeholder text, resting state of destructive controls | 4.83:1 on white, 4.59:1 on `#F8F9FB` — passes AA text on both |
| Subtle surface | `#EEF0F5` | background (12), text (1) | subtle surfaces, dividers, inactive chips; text only on primary navy (14.84:1) | not a text colour on light surfaces |
| Gold hover | `#E0B62E` | background (6) | hover state of gold surfaces only | 8.78:1 against primary navy; same light-surface text prohibition as `#C9A227` |
| Muted placeholder | `#9CA3AF` | placeholder text (1) | **non-text roles only** — see the defect note below | **2.54:1 on white, 2.41:1 on `#F8F9FB` — MUST NOT be used as text, including placeholder text** |
| Navy tint 1 | `#1A3060` | background (2), gradient stop (1) | elevated navy surfaces, gradient stops | carries white and gold text compliantly |
| Navy tint 2 | `#1A2F5A` | background (2), gradient stop (1) | elevated navy surfaces, gradient stops | 13.14:1 with white text |
| Navy tint 3 | `#2A4070` | background (1) | elevated navy surfaces | verify per pairing |
| Navy tint 4 | `#162D5E` | background (1) | elevated navy surfaces | verify per pairing |
| Navy alpha 06 | `rgba(13,27,61,0.06)` | borders (29), divide (1) | hairline borders and dividers on light surfaces | non-text |
| Navy alpha 08 | `rgba(13,27,61,0.08)` | borders (13) | borders on light surfaces | non-text |
| Navy alpha 10 | `rgba(13,27,61,0.10)` | borders (18), incl. form fields | form-field and card borders | non-text; must meet 3:1 where it bounds a control |
| Navy alpha 15 | `rgba(13,27,61,0.15)` | borders (10), background (1) | stronger borders, subtle overlays | non-text |
| Navy alpha 20 | `rgba(13,27,61,0.20)` | border (1) | strongest hairline border | non-text |

**Ratified defect note — muted placeholder.** The reference applies `#9CA3AF` as placeholder text
at 2.54:1, which fails WCAG 2.2 AA. The reference is internally inconsistent here: it also applies
`#6B7280` as placeholder text elsewhere, at 4.83:1. Placeholder text MUST therefore use `#6B7280`.
`#9CA3AF` remains ratified as a verified observable value but is restricted to non-text roles. This
correction is drawn from the reference's own palette; no replacement colour may be invented.

**Gradient rule.** Only gradients composed of ratified values and observed in the reference are
permitted — the navy gradient stops and the single gold gradient stop. No other gradient may be
introduced (Principle II.5).

### Ratified Non-Colour Tokens

| Token | Approved value |
| --- | --- |
| Primary typeface (Arabic and interface) | Cairo, self-hosted |
| Secondary typeface (Latin content only) | Poppins, self-hosted |
| Base spacing unit | 8px |
| Primary corner radius | 12px |
| Desktop reference width | 1440px |
| Desktop grid | 12 columns |
| Shadows | Soft and restrained — built from the navy alpha tokens above |
| Layout properties | Logical (inline/block start and end), direction-aware by construction |

**Typography deviation note.** The published reference is a Latin-language design. The Cairo
primary typeface is a deliberate, ratified deviation required by the `ar-EG` and RTL mandate of
Principle XX, and takes precedence over the reference's typeface choice. All other typographic
character — scale relationships, weight contrast, tracking discipline, and hierarchy — MUST
still follow the reference under Principle I.

### Reference Observations Pending Re-Verification

Recorded under a prior grounding pass, before Principle XIX existed. Advisory only until
re-confirmed under Principle XIX; MUST NOT be cited as grounding evidence in the meantime
(Principle I.8).

| Observation | Status |
| --- | --- |
| The reference Hero image does not clearly depict a smart door lock; the Hero composition should stay faithful while its image is replaced with a verified ZAKEY smart-lock image sourced under Principle V | Pending re-verification |
| The eighteen-value colour extraction and the per-token usage counts recorded above | Values binding; per-page and per-state roles pending re-confirmation |

### Ratified Egyptian Commerce Parameters

| Parameter | Value | Binding rule |
| --- | --- | --- |
| Currency display | `ج.م` | XX.4 — one centralized formatter |
| VAT | 14% | XX.6 — shared, tested calculation routine |
| Free-shipping threshold | 1,500 EGP | XX.7 — same shared routine |
| Governorate coverage | All 27 Egyptian governorates | XX.11 |
| Phone validation | Egyptian format, server-side | XX.12 |
| Address capture | Detailed address fields plus a landmark field | XX.13 |
| Same-day delivery | Greater Cairo, configuration-driven | XX.14 |
| Installation service | Greater Cairo and Alexandria, configuration-driven | XX.15 |
| Hotline | `19919` — centrally configurable, provenance-recorded | XX.16 |
| Location | New Cairo — centrally configurable, provenance-recorded | XX.16 |
| Catalog price evidence | Approximately 2,190-7,490 EGP | XX.10 — advisory evidence only, never a production fact |
| Money representation | Decimal, centralized rounding | VI.11, XX.8 |

### Approved Payment Presentation

Cash on Delivery; Vodafone Cash; e& Cash / Etisalat Cash; CashU; InstaPay transfer; and
Egyptian bank-card installment presentation for 6 and 12 months. Presentation is governed by
Principle XXI; nothing in this list authorizes presenting an unimplemented integration as
active.

### Mandatory Verification Widths

| Width | Class |
| --- | --- |
| 1440px | Desktop reference |
| 1024px | Tablet |
| 768px | Transition |
| 390px | Mobile |

### Approved Stack

Python 3.12; Django 5.2 LTS; Django templates and reusable partials; PostgreSQL-compatible
architecture; Tailwind CSS compiled locally; native JavaScript ES modules; locally hosted Cairo
and Poppins fonts; locally served Lucide or project-owned SVG icons; progressive enhancement;
server-side validation; decimal-safe monetary calculations; centralized formatting and business
calculations; pytest; pytest-django; Playwright; axe accessibility testing; Ruff; Prettier;
Vitest with jsdom where valuable for isolated JavaScript behavior.

These are binding unless a later approved architectural decision provides documented evidence
for a change, recorded through the amendment procedure in **Governance**.

### Prohibited Without Amendment

React; Vue; Angular; Bootstrap; jQuery; the Tailwind CDN; font CDNs; icon CDNs; copied Figma
runtime code; large UI frameworks or libraries that would replace the ZAKEY design system; dark
mode; and fake or inert frontend behavior presented as working.

## Development Workflow and Quality Gates

### Stage Gates

Work proceeds through these fifteen ordered gates. A later gate MUST NOT begin while a blocking
inconsistency remains in an earlier one (Principle XI.10). A gate that does not apply MUST be
recorded as not applicable, with a reason.

| # | Gate | Leaves the gate when |
| --- | --- | --- |
| 1 | Repository and governance audit | Repository state, branch, tooling, and governance documents inspected and recorded |
| 2 | Constitution correction | Constitution consistent, versioned, and free of contradictions |
| 3 | Targeted visual grounding | Principle XIX satisfied for every surface about to be specified |
| 4 | Specification | The Specification row of the Gate Matrix below is satisfied |
| 5 | Clarification of material ambiguity | Every material ambiguity resolved and recorded (XI.3) |
| 6 | Technical plan | Per-principle constitution check for I-XXI complete with cited evidence |
| 7 | Requirements checklist | Checklist generated with its Definition-of-Done block intact |
| 8 | Tasks | Every task traceable to a requirement and an acceptance criterion; ownership and concurrency boundaries assigned (XVI) |
| 9 | Cross-artifact analysis | Missing, contradictory, duplicated, untestable, and non-compliant items identified |
| 10 | Correction of all material analysis findings | Every material finding corrected — not deferred |
| 11 | Implementation | Approved scope built with no silent redefinition and no concurrent edits to shared surfaces |
| 12 | Automated verification | Applicable items from XII.2 executed with exact commands and exact results |
| 13 | Visual QA | Screenshots captured **and inspected** at all four widths, compared against Principle XIX evidence |
| 14 | Two critique-and-correction passes | Both passes documented, with what changed in each |
| 15 | Final acceptance report | All twenty conditions of Principle XVIII satisfied and reported |

No implementation may begin merely because a `tasks.md` file exists. Gates 9 and 10 MUST pass
first.

### Gate Matrix

| Stage | MUST be satisfied before leaving the stage |
| --- | --- |
| Visual grounding | Per-surface browser inspection at all four widths, evidence recorded and dated (XIX) |
| Specification | Out-of-scope section present (XI.9); measurable acceptance criteria (XII.1); UI inventory for UI work (XIII.1); performance budgets where relevant (IX.7); reference-fidelity verification method (I.6); grounding evidence cited per surface (XIX.5); Arabic/RTL and Egyptian-market requirements stated (XX); integration-honesty stance stated (XXI) |
| Clarification | Every material ambiguity resolved and recorded (XI.3) |
| Plan | Per-principle constitution check for I-XXI; assessment recorded for every new dependency (III.4); complexity justifications recorded |
| Tasks | Every task traceable to a requirement and an acceptance criterion (XI.5); ownership and concurrency boundaries assigned (XVI.6, XVI.7) |
| Analysis | Missing, contradictory, duplicated, untestable, and non-compliant items identified (XI.6) |
| Implementation | No silent redefinition of requirements (XI.7); no concurrent edits to shared surfaces (XVI.7) |
| Verification | Applicable items from XII.2 executed with exact commands and exact results; two visual critique passes for major storefront work (XIII.3); guard skills run where in scope (XIV.10) |
| Acceptance | All twenty conditions of Principle XVIII satisfied |

### Delegation Rules

Delegation follows Principle XVI. Each delegated unit of work MUST state its exact scope, its
owner, the files it may modify, the files it may not modify, the acceptance evidence it must
return, and the tests it must run. Two agents MUST NOT be assigned overlapping write scopes.

### Evidence

Verification evidence — commands, outcomes, inspected-screenshot observations, grounding
records, accessibility findings, and known limitations — MUST be written into the owning Spec
Kit artifacts, per Principle XVII. Evidence that exists only in conversation is not evidence.

## Governance

### Supersession

This constitution supersedes conflicting informal project-development preferences,
conventions inherited from the legacy repository, and any default behavior of the tools used
to build this project. Where a tool default and this constitution disagree, this constitution
wins. This explicitly includes tooling hooks that would perform a Git operation Principle XV
prohibits.

### Compliance Review

Every specification, plan, and task set MUST include a constitution-compliance check covering
Principles I-XXI. A constitutional violation MUST be corrected before the affected feature
is accepted; it MUST NOT be deferred to a later feature.

### Amendment Procedure

Every amendment MUST document:

1. the changed principle,
2. the reason for the change,
3. migration or remediation impact,
4. affected specifications,
5. the new constitution version, and
6. the amendment date.

An amendment takes effect only once it is written into this file and the version footer is
updated.

### Versioning Policy

Constitution versioning follows semantic versioning:

- **MAJOR** — incompatible governance changes, including removal or redefinition of a
  principle in a way that invalidates prior compliance.
- **MINOR** — a new principle, or materially expanded rules within an existing principle.
- **PATCH** — clarifications, wording, and non-semantic refinements that do not change
  existing intent.

### Exceptions

An exception to any rule in this constitution MUST be explicit, narrowly scoped, justified,
approved by the user, and documented in the relevant artifacts. An undocumented deviation is
a violation, not an exception. Complexity that conflicts with these principles MUST be
justified in the relevant plan's complexity-tracking section.

### Vendor Neutrality

This constitution MUST NOT be amended in a way that permanently binds the project to one
commercial model, one AI vendor, or one assistant product. Ownership is defined by capability
tier and named role under Principle XVI. Naming a specific product as the current active lead
is a statement of fact about the present stage, not a permanent binding.

### Scope of Application

This constitution applies to the public storefront and to every future backend, admin,
commerce, integration, deployment, and maintenance specification produced for the ZAKEY
platform in this repository.

**Version**: 2.0.0 | **Ratified**: 2026-07-31 | **Last Amended**: 2026-08-01
