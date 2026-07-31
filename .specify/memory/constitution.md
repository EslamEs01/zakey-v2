<!--
SYNC IMPACT REPORT
==================
Version change: 1.0.1 → 1.1.0
Amendment date: 2026-07-31
Bump rationale (1.0.1 → 1.1.0, MINOR): Materially expanded rules within an existing principle.
Principle II's ratified design-token table grew from five colour values to eighteen, after every
designer-chosen colour literal in the approved visual reference was extracted, classified, and
contrast-tested. The table now governs five core brand tokens and thirteen reference-derived
support tokens, each with its observable reference role, its permitted semantic uses, and its
measured contrast limitation. Also added: a provenance rule distinguishing designed colours from
inherited framework defaults, a gradient rule, and a ratified defect note restricting `#9CA3AF`
to non-text roles.

This is backward compatible — no principle was removed or redefined, no prior compliance is
invalidated, and every previously ratified value keeps its exact hexadecimal value and meaning.
Under the Versioning Policy, "materially expanded rules within an existing principle" is MINOR,
so a PATCH would be insufficient.

Colour-governance impact: zero palette decisions remain open. Support tokens are binding, not
advisory, and `/speckit-plan` MUST NOT reconsider, substitute, or re-approve any ratified colour.
The plan's remaining colour work is implementation mapping and token naming only.

Prior entry — Version change: 1.0.0 → 1.0.1
Bump rationale (1.0.0 → 1.0.1, PATCH): Resolution of a recorded placeholder only. The
deferred TODO(LEGACY_REPO_PATH_CONFIRMATION) is closed — the user has explicitly confirmed
`/media/mekky/work/backend/zakey.v1` as the verified legacy repository and the authoritative
initial product-content source. No principle was added, removed, or redefined; no governance
intent changed; no prior compliance is invalidated. Under the Versioning Policy this is a
clarification, therefore PATCH.
Prior entry — Version change: (uninitialized template) → 1.0.0
Bump rationale: Initial ratified adoption. The file previously contained only unfilled
template placeholders; this is the first governance document in force for this project.

Modified principles: none (no prior ratified principles existed).

Added sections:
  - Core Principles: I–XVIII (18 principles)
      I.     Reference-Led Visual Fidelity
      II.    Permanent ZAKEY Brand System
      III.   Approved Technical Foundation
      IV.    Clean-Room Architecture
      V.     Content and Asset Integrity
      VI.    Functional Completeness
      VII.   Responsive Design
      VIII.  Accessibility
      IX.    Performance and Frontend Quality
      X.     Security, Privacy, and Data Safety
      XI.    Specification-First Development
      XII.   Test-First Acceptance
      XIII.  Visual QA and Consistency
      XIV.   Code Quality
      XV.    Git and Repository Safety
      XVI.   Claude Code Governance
      XVII.  LeanCtx and Context Discipline
      XVIII. Definition of Done
  - Canonical Project Facts (template slot SECTION_2) — authoritative registry of
    repositories, reference URL, design tokens, verification widths, and approved stack.
  - Development Workflow and Quality Gates (template slot SECTION_3) — lifecycle
    sequence, gate matrix, delegation rules, evidence requirements.
  - Governance — supersession, compliance review, amendment procedure, versioning policy,
    exceptions, scope of application (fulfils the requested 19th principle,
    "Governance and Amendments").

Removed sections: all bracketed template placeholders and their example comments.

Templates requiring updates:
  ✅ aligned  .specify/templates/spec-template.md          (2026-07-31)
       Now requires Purpose and Product Outcome, Authoritative Sources and Evidence, page /
       component / interaction / responsive / state inventories (XIII.1), Content and Asset
       Integrity (V), Reference-Fidelity Requirements with a stated verification method (I.6),
       Accessibility (VIII), Performance Budgets (IX.7), Repository Readiness Preconditions,
       Explicit Out of Scope (XI.9), Constitution Compliance, and requirement traceability.
  ✅ aligned  .specify/templates/plan-template.md          (2026-07-31)
       "Constitution Check" is now an explicit per-principle gate table for I–XVIII requiring
       cited evidence per principle, plus an initial and a post-design re-check, and a
       blocking-violations register that must be empty before Phase 0 research proceeds.
  ✅ aligned  .specify/templates/tasks-template.md         (2026-07-31)
       The "Tests are OPTIONAL" instruction is removed. Verification tasks are now required
       wherever the owning specification or Principle XII makes them applicable, with explicit
       categories for Django system checks, Python and JavaScript tests, Playwright, axe,
       manual keyboard inspection, broken-link and console-error checks, responsive-overflow
       checks, production asset build, screenshot capture AND inspection, two visual critique
       passes, guard skills, and exact final verification commands and results.
  ✅ aligned  .specify/templates/checklist-template.md     (2026-07-31)
       Now carries the fifteen conditions of Principle XVIII as a required section.
  Note: the ratifying invocation was restricted to constitution files, so no template was
  edited then. All four were aligned in the 2026-07-31 pre-planning readiness pass. Template
  alignment does not itself change governance and therefore carries no version bump beyond the
  PATCH recorded above.

Deferred items / TODOs:
  (none open)

Resolved items:
  ✅ TODO(LEGACY_REPO_PATH_CONFIRMATION) — CLOSED 2026-07-31, constitution v1.0.1.
    The ratifying instruction named the legacy repository as
    `/media/mekky/work/backend/zakey`. That path does not exist on disk (verified 2026-07-31,
    and re-verified during the readiness pass). The verified ZAKEY legacy repository is
    `/media/mekky/work/backend/zakey.v1` — a Django project containing apps/, config/,
    static/, media/, locale/, specs/, and reference-imports/, HEAD 5fdd81d, working tree
    clean. The user explicitly confirmed this repository as the verified legacy project and
    as the authoritative initial product-content source for Feature 001. No substitution
    ambiguity remains; asset extraction under Principle V is authorized.
-->

# ZAKEY Premium Smart Lock Storefront Constitution

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
   hierarchy, page composition, section order where appropriate, proportions, spacing
   rhythm, typography character, component language, product presentation, and restrained
   luxury appearance.
2. Small creative improvements MAY be introduced, and only when they demonstrably improve
   usability, accessibility, responsiveness, product relevance, interaction clarity, or
   visual quality. Each such improvement MUST be recorded in the owning specification with
   the improvement claimed and the reason for it.
3. Creative improvements MUST NOT transform the storefront into a different visual
   identity. A change that alters the brand palette, the typographic character, the layout
   density, or the overall design language is an identity change, not an improvement, and
   requires a constitutional amendment.
4. Obvious errors in the reference MUST NOT be reproduced merely to achieve pixel
   similarity. Where the reference is wrong, the specification MUST state the defect, the
   correction, and the justification.
5. The reference Hero image does not clearly depict a smart door lock. The Hero composition
   SHOULD remain faithful to the reference, and its image MUST be replaced with a verified,
   high-quality ZAKEY smart-lock image sourced under Principle V.
6. Every UI specification MUST define how reference fidelity will be inspected and verified,
   naming the pages compared, the widths compared at, and the acceptance threshold used.
7. Every page MUST belong to one coherent ZAKEY design system. Page-specific visual
   identities are forbidden.

*Rationale:* The reference encodes an approved premium direction that the project is not
free to reinvent page by page. Fidelity is the default; deviation is a documented decision.

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
4. The interface MUST read as premium, modern, minimal, elegant, trustworthy, technical, and
   luxurious without visual excess. Compliance is decided at the visual critique passes
   required by Principle XIII, not by the implementer's self-assessment.
5. The project MUST NOT introduce, absent a constitutional amendment: dark mode; black or
   near-black full-bleed sections that read as an accidental dark theme; generic
   AI-generated styling; excessive gradients; excessive glassmorphism; random decorative
   elements; inconsistent colors; arbitrary spacing; oversized empty areas; repetitive
   promotional sections; excessive animation; mismatched components; or page-specific
   visual identities.
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

*Rationale:* A single ratified token set is what makes twenty pages look like one product.
Rule 7 exists because the brand palette and the accessibility target would otherwise
silently conflict; the conflict is resolved once, here, rather than page by page.

### III. Approved Technical Foundation

1. The approved stack is the list recorded in **Canonical Project Facts**. Adopting any
   technology outside that list requires a constitutional amendment.
2. The project MUST NOT use, absent an approved amendment: React, Vue, Angular, Bootstrap,
   jQuery, the Tailwind CDN build, font CDNs, icon CDNs, code copied from a Figma runtime
   export, or large UI libraries that would replace the ZAKEY design system.
3. Production assets MUST be compiled locally. A production page MUST NOT depend on a
   runtime CDN for CSS, JavaScript, fonts, or icons. Verification: no third-party origin
   appears in a network trace of a production-mode page load, and no `<link>` or `<script>`
   element in a rendered template points at a third-party origin.
4. Every new dependency MUST have a documented purpose and MUST be assessed, in the owning
   plan, for maintenance cost, security exposure, runtime performance, and bundle-size
   impact. A dependency added without that record MUST be removed or retroactively
   documented before acceptance.
5. Fonts MUST be self-hosted from files stored in the repository or produced by the build.

*Rationale:* The stack is deliberately small and locally compiled so the storefront stays
fast, auditable, and free of third-party runtime dependencies ZAKEY does not control.

### IV. Clean-Room Architecture

1. The legacy project's frontend implementation, templates, CSS architecture, JavaScript
   architecture, and design system MUST NOT be copied into this repository.
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
9. The architecture MUST support future localization and RTL — externalized strings,
   direction-aware layout primitives, and no layout that assumes LTR-only geometry — without
   introducing a language selector into the current interface, which is not approved.

*Rationale:* This is a rebuild, not a port. The value of starting over is lost if legacy
structure is carried across, and lost again if the new structure decays into per-page
duplication.

### V. Content and Asset Integrity

1. All visible content MUST be truthful, relevant, and appropriate for ZAKEY smart locks and
   smart-home products.
2. Verified content and assets from the legacy repository SHOULD be reused where available,
   copied out under the read-only constraint of Principle IV.
3. The project MUST NOT invent awards, certifications, partnerships, integrations, customer
   numbers, sales totals, review counts, customer reviews, ratings, technical
   specifications, warranties, delivery promises, media coverage, trust badges, or business
   addresses.
4. Any claim that cannot be traced to a verified source MUST be removed or replaced with
   conservative, product-focused wording.
5. Visible interfaces MUST NOT contain the words "demo", "placeholder", "Figma", "Jazzmin",
   or any other internal development terminology — in copy, alt text, titles, ARIA labels,
   user-visible filenames, or metadata.
6. Placeholder images MUST NOT remain in an accepted release.
7. Product images MUST preserve their correct aspect ratio and MUST NOT appear stretched,
   damaged, incorrectly cropped, or visibly degraded.
8. Asset sources, ownership, and licensing assumptions MUST be documented in the owning
   specification or in a dedicated asset manifest.

*Rationale:* A storefront that invents credibility signals is both a legal exposure and a
trust failure. Conservative truthful copy is always acceptable; fabricated proof never is.

### VI. Functional Completeness

1. Every visible control MUST have intentional behavior — buttons, links, icons, inputs,
   tabs, menus, filters, selectors, drawers, dialogs, carousel controls, quantity controls,
   forms, and commerce actions.
2. Dead controls are forbidden. A control that renders but does nothing MUST either be
   implemented or removed.
3. `href="#"` is forbidden in a finished interface.
4. Fake success states are forbidden. A success message MUST NOT be shown unless the
   underlying operation actually succeeded.
5. Internal navigation MUST use valid named Django URLs resolved through `{% url %}` or an
   equivalent reverse lookup. Hardcoded internal paths are forbidden.
6. Forms MUST provide server-side validation, appropriate client-side assistance, loading
   states where applicable, clear validation errors, success states, and failure states.
7. Loading, empty, unavailable, disabled, error, and success states MUST be intentionally
   designed wherever they are reachable.
8. Commerce prices and totals MUST originate from authoritative data and MUST be calculated
   by one shared, tested routine. Two surfaces MUST NOT compute the same total differently.
9. Frontend payment simulations MUST NOT request, collect, transmit, log, or persist real
   card details.
10. Future real payments MUST be handled by a compliant payment gateway. ZAKEY MUST NEVER
    store prohibited payment credentials, including full card numbers, CVV/CVC values, PINs,
    or magnetic-stripe data.

*Rationale:* A storefront is judged by whether things work when clicked. Half-wired UI is
worse than absent UI, because it teaches customers the site is unreliable.

### VII. Responsive Design

1. Every public page and every reusable component MUST be intentionally designed and
   verified at the four widths recorded in **Canonical Project Facts**: 1440px desktop,
   1024px tablet, 768px transition, 390px mobile.
2. Responsive implementation MUST NOT consist only of stacking desktop columns. Each width
   MUST receive a deliberate layout decision.
3. An accepted interface MUST exhibit none of the following at any of the four widths:
   horizontal overflow, clipped content, header collisions, overlapping floating elements,
   tablet dead zones, inaccessible navigation, unreadable product cards, unstable image
   sizing, oversized empty sections, unusable mobile forms, or unusable mobile checkout.
4. Absence of horizontal overflow MUST be verified programmatically, by asserting that the
   document scroll width does not exceed the viewport width at each of the four widths.
5. Mobile navigation, filters, galleries, tables, drawers, dialogs, and checkout actions MUST
   each receive dedicated responsive behavior, specified before implementation.

*Rationale:* Most storefront traffic is not desktop. Tablet is where naive responsive work
fails first, which is why 1024px and 768px are both mandatory checkpoints.

### VIII. Accessibility

1. The project MUST target WCAG 2.2 Level AA wherever applicable.
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
5. Accessibility MUST be verified by both automated axe checks and manual keyboard-focused
   inspection covering tab order, focus visibility, focus trapping in dialogs and drawers,
   and escape or dismiss behavior.
6. Automated accessibility checks alone are insufficient for final acceptance. A feature with
   a clean axe run and no manual keyboard pass is not accessibility-verified.

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
   MUST NOT be disabled for untrusted content.
7. Authentication, authorization, and administration MUST follow least privilege when
   introduced.
8. Personal information MUST NOT be exposed to unauthorized users, including through URLs,
   enumerable identifiers, API responses, or error output.
9. Logs MUST NOT contain passwords, payment credentials, authentication secrets, session
   secrets, or unnecessary personal information.
10. Destructive operations MUST require explicit authorization, a suitable confirmation step,
    and appropriate auditability.

*Rationale:* Commerce software holds other people's money and identities. These are the
minimum controls under which such software may be accepted.

### XI. Specification-First Development

1. Project work MUST follow this sequence wherever applicable: Constitution → Specification →
   Clarification → Plan → Checklist → Tasks → Cross-artifact analysis → Implementation →
   Verification → Convergence and correction.
2. A specification MUST define required outcomes and behaviors before implementation begins.
3. Material ambiguity MUST be resolved before planning. An ambiguity is material when two
   reasonable readings would produce materially different work.
4. Plans MUST demonstrate compliance with this constitution through an explicit per-principle
   constitution check.
5. Tasks MUST be traceable to specific requirements and acceptance criteria.
6. Cross-artifact analysis MUST identify missing requirements, contradictions, duplicated
   requirements, untestable acceptance criteria, missing edge cases, and constitutional
   violations.
7. Implementation MUST NOT silently redefine approved requirements.
8. A material scope change MUST first be reflected in the approved specification, plan, and
   tasks, and only then implemented.
9. Every specification MUST explicitly identify what is out of scope.

*Rationale:* Ambiguity resolved during implementation is resolved by whoever is typing,
without review. Resolving it in the specification is what makes review possible.

### XII. Test-First Acceptance

1. Every feature specification MUST define measurable acceptance criteria before
   implementation begins.
2. Verification MUST include the applicable combination of: Django system checks; Python
   tests; model tests; service tests; form tests; view tests; permission tests;
   template-rendering tests; JavaScript behavior tests; Playwright end-to-end tests; axe
   accessibility tests; broken-link checks; console-error checks; responsive-overflow
   checks; a production asset build; and visual screenshots. The owning specification MUST
   state which of these apply and MUST justify each exclusion.
3. Bug fixes SHOULD include a regression test whenever technically practical.
4. A feature MUST NOT be reported as complete when required tests were not run, required
   tests are failing, failures were hidden or ignored, results were estimated rather than
   observed, visual evidence was captured but not inspected, or known limitations were
   omitted from the report.
5. "Implemented" and "verified" MUST be reported as two separate facts. Reporting an
   unverified implementation as complete is a constitutional violation.
6. Reported results MUST include the exact commands executed and their exact outcomes.
   Paraphrased or reconstructed results are forbidden.

*Rationale:* The most damaging failure mode in agent-driven development is a confident
completion report for unverified work. Rules 4–6 exist to make that failure impossible to
commit accidentally.

### XIII. Visual QA and Consistency

1. Every UI specification MUST include an inventory of pages, components, responsive states,
   empty states, error states, and interactions.
2. Screenshots MUST be captured at the approved desktop, tablet, and mobile widths.
3. Major storefront work MUST undergo at least two visual critique and correction passes
   after initial implementation.
4. Visual inspection MUST cover every affected page, not only the homepage.
5. Repeated components MUST be compared across pages for dimensions, spacing, colors,
   typography, focus states, responsive behavior, and interaction behavior. Divergence
   between two instances of the same component is a defect.
6. Capturing screenshots without inspecting them does not count as visual QA. The
   verification record MUST state what was observed in each inspected screenshot.
7. Any unapproved deviation from the reference design direction MUST be corrected, or
   truthfully documented and raised for a decision.

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
2. Claude MAY create the required local feature branch.
3. Unless the user explicitly requests it in the current session, Claude MUST NOT commit,
   push, open pull requests, merge, modify remotes, delete branches, rewrite history, or
   perform any remote GitHub operation.
4. Existing user changes MUST be preserved. Uncommitted user work MUST NOT be discarded,
   stashed, reverted, or overwritten.
5. Unrelated files MUST NOT be modified or reformatted. A formatting pass MUST be confined to
   files the current task legitimately touches.
6. Secrets, databases, uploaded media, test recordings, temporary screenshots, dependency
   caches, and generated artifacts MUST be covered by the repository ignore policy and MUST
   NOT be committed.
7. The final report of any session MUST truthfully list every Git action performed, and MUST
   state explicitly when none were performed.

*Rationale:* Version-control actions are the hardest to undo and the easiest to perform by
reflex. Authority for them stays with the user.

### XVI. Claude Code Governance

1. Claude Code owns the complete project workflow: analysis, specification, planning,
   implementation, testing, visual review, correction, and final verification. No other
   assistant or external agent is the project owner. Where other tools exist in this
   environment — including Codex, Kimi, CodeRabbit, or any similar assistant — they MAY be
   used only when the user explicitly requests them; their output is advisory evidence only;
   and Claude Code retains ownership and final responsibility.
2. Claude Opus is the lead product analyst, architect, specification owner, planning
   authority, orchestration authority, integration owner, difficult-problem implementer,
   design-quality owner, reviewer, and final verification authority.
3. Claude Opus MUST retain personal responsibility for interpreting requirements;
   architectural decisions; design-system decisions; shared design tokens; shared components;
   database architecture; sensitive migrations; authentication and permissions; payment
   architecture; difficult debugging; integration; final visual decisions; and final
   verification. These MUST NOT be fully delegated.
4. Claude Opus MAY delegate bounded work to Claude agents. Recommended allocation:
   - Opus agents — architecture, sensitive migrations, complex backend work, advanced
     debugging, critical design work, security, concurrency, and final reviews.
   - Sonnet agents — routine implementation, Django views, forms, templates, page
     construction, CRUD work, tests, and clear corrective work.
   - Haiku agents — read-only exploration, inventories, asset discovery, documentation
     inspection, and simple isolated analysis.
5. Delegated work MUST be bounded in scope and MUST have one explicit owner.
6. Multiple agents MUST NOT concurrently edit the same shared templates, design tokens,
   global CSS, shared JavaScript, migrations, or central configuration.
7. Findings from delegated agents MUST be reviewed and integrated by the lead. Agent output
   is evidence, not automatic acceptance.
8. Claude Opus remains responsible for the correctness, consistency, and completeness of all
   delegated work.
9. Claude MUST NOT stop merely because one agent completed its assigned task. Claude MUST
   continue through the approved scope until all tasks are complete, integration is complete,
   tests have run, visual QA has run, failures have been corrected, and final verification
   has completed — unless a genuine blocker requires user authority or a material product
   decision.

*Rationale:* Delegation multiplies output and dilutes accountability unless ownership is
named. This principle names it.

### XVII. LeanCtx and Context Discipline

1. LeanCtx MUST be used throughout large project work when it is available.
2. Before major repository exploration, Claude SHOULD verify the LeanCtx connection and
   status.
3. Claude and its agents MUST avoid repeatedly loading the same large files without a
   justified need.
4. Repository exploration SHOULD be targeted and evidence-driven rather than exhaustive.
5. Context compression MUST NOT be used as an excuse to lose approved requirements,
   architectural decisions, task status, test evidence, or known blockers.
6. Important decisions and verification evidence MUST be written into the appropriate Spec
   Kit artifacts rather than left only in conversation context.

*Rationale:* Anything that exists only in a conversation is lost at the next compaction.
Durable artifacts are the project's memory.

### XVIII. Definition of Done

A specification is complete only when all of the following hold:

1. All in-scope requirements are implemented.
2. Every requirement is traceable to an acceptance criterion.
3. All required tests pass.
4. All required manual checks are completed.
5. All required visual checks are completed.
6. All captured screenshots have been inspected, and the observations are recorded.
7. Responsive behavior is verified at all four approved widths.
8. Accessibility is verified by both automated and manual means.
9. Production assets build successfully.
10. No dead controls remain.
11. No unexpected console errors remain.
12. Documentation is current.
13. Known limitations are truthfully recorded.
14. Unrelated user work remains untouched.
15. The final report includes the exact commands executed and their exact results.

Passing only a subset of the required tests does not satisfy this Definition of Done. Work
that meets fourteen of these fifteen conditions is not done.

*Rationale:* "Done" must be a checklist with a single interpretation, or it becomes a
judgment call made by whoever wants to stop working.

## Canonical Project Facts

This section is the authoritative registry referenced by Principles I, II, III, IV, and VII.
Changing any value here requires a constitutional amendment.

### Identity and Locations

| Fact | Value |
| --- | --- |
| Project name | ZAKEY Premium Smart Lock Storefront |
| Target repository (read-write) | `/media/mekky/work/backend/zakey-v2` |
| Legacy repository (STRICTLY READ-ONLY) | `/media/mekky/work/backend/zakey.v1` |
| Primary visual reference | `https://remote-fried-86528699.figma.site/` |

The legacy repository MAY be inspected only to obtain verified ZAKEY logos, brand assets,
product images, product information, categories, collections, and truthful business content.
It MUST NOT be modified in any way. This path is confirmed: `/media/mekky/work/backend/zakey`
does not exist, `/media/mekky/work/backend/zakey.v1` is the verified legacy ZAKEY Django
project (HEAD 5fdd81d), and the user has confirmed it as the authoritative initial
product-content source. No path confirmation remains outstanding as of v1.0.1.

### Ratified Design Tokens

This is the complete ratified ZAKEY colour system. It was expanded from five to eighteen values
in v1.1.0 after every designer-chosen colour literal in the approved reference was extracted and
classified. **Core brand tokens** carry the brand identity; **reference-derived support tokens**
are equally binding parts of the approved visual system, not optional suggestions. No colour
outside this table may appear in an accepted interface, and every value here MUST be implemented
through one centralized token source (Principle II.2).

Provenance rule: the designed palette is every colour the reference author chose explicitly — that
is, every arbitrary-value colour literal in the published reference. Colours inherited from
framework defaults (unprefixed utility classes) are **not** part of the ratified system, except
`#FFFFFF`, which is unambiguous and independently ratified. A colour whose only observed use is in
content this project removes as fabricated, or defers to a later feature, is not ratified.

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
| Typography | Poppins, self-hosted |
| Base spacing unit | 8px |
| Primary corner radius | 12px |
| Desktop reference width | 1440px |
| Desktop grid | 12 columns |
| Shadows | Soft, restrained, premium — built from the navy alpha tokens above |

### Mandatory Verification Widths

| Width | Class |
| --- | --- |
| 1440px | Desktop reference |
| 1024px | Tablet |
| 768px | Transition |
| 390px | Mobile |

### Approved Stack

Django 5.2 LTS; Django templates; Tailwind CSS compiled locally; native JavaScript modules;
locally installed Poppins fonts; local SVG icons or locally installed Lucide icons;
PostgreSQL once persistent production data is introduced; pytest; pytest-django; Playwright;
axe accessibility testing; Ruff; Prettier.

### Prohibited Without Amendment

React; Vue; Angular; Bootstrap; jQuery; the Tailwind CDN; font CDNs; icon CDNs; copied Figma
runtime code; large UI libraries that would replace the ZAKEY design system; dark mode.

## Development Workflow and Quality Gates

### Lifecycle

Work proceeds in the order defined by Principle XI: Constitution → Specification →
Clarification → Plan → Checklist → Tasks → Cross-artifact analysis → Implementation →
Verification → Convergence and correction. A stage MUST NOT be skipped where it applies; a
stage that does not apply MUST be recorded as not applicable, with a reason.

### Gate Matrix

| Stage | MUST be satisfied before leaving the stage |
| --- | --- |
| Specification | Out-of-scope section present (XI); measurable acceptance criteria (XII); UI inventory for UI work (XIII); performance budgets where relevant (IX); reference-fidelity verification method (I) |
| Clarification | Every material ambiguity resolved and recorded (XI) |
| Plan | Per-principle constitution check for I–XVIII; assessment recorded for every new dependency (III); complexity justifications recorded |
| Tasks | Every task traceable to a requirement and an acceptance criterion (XI); ownership and concurrency boundaries assigned (XVI) |
| Analysis | Missing, contradictory, duplicated, untestable, and non-compliant items identified (XI) |
| Implementation | No silent redefinition of requirements (XI); no concurrent edits to shared surfaces (XVI) |
| Verification | Applicable items from XII executed with exact commands and exact results; two visual critique passes for major storefront work (XIII); guard skills run where in scope (XIV) |
| Acceptance | All fifteen conditions of Principle XVIII satisfied |

### Delegation Rules

Delegation follows Principle XVI. Each delegated unit of work MUST state its scope, its
owner, the files it may modify, and the evidence it must return. Two agents MUST NOT be
assigned overlapping write scopes.

### Evidence

Verification evidence — commands, outcomes, inspected-screenshot observations, accessibility
findings, and known limitations — MUST be written into the owning Spec Kit artifacts, per
Principle XVII. Evidence that exists only in conversation is not evidence.

## Governance

### Supersession

This constitution supersedes conflicting informal project-development preferences,
conventions inherited from the legacy repository, and any default behavior of the tools used
to build this project. Where a tool default and this constitution disagree, this constitution
wins.

### Compliance Review

Every specification, plan, and task set MUST include a constitution-compliance check covering
Principles I–XVIII. A constitutional violation MUST be corrected before the affected feature
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

### Scope of Application

This constitution applies to the public storefront and to every future backend, admin,
commerce, integration, deployment, and maintenance specification produced for the ZAKEY
platform in this repository.

**Version**: 1.1.0 | **Ratified**: 2026-07-31 | **Last Amended**: 2026-07-31
