<!--
Sync Impact Report
- Version change: 1.0.0 -> 1.1.0
- Added principles:
  - I. Frontend Approval Gate and Scope Isolation
  - II. Reference Fidelity and Governed Design System
  - III. Arabic-First Accessible Responsive Experience
  - IV. Replaceable Prototype Data and Progressive Enhancement
  - V. Evidence-Based Quality Gates
- Added sections: Frontend Technology and Product Constraints; Delivery Workflow and Review Gates
- Removed sections: none; template placeholders replaced
- Templates reviewed:
  - ✅ .specify/templates/constitution-template.md (generic template remains valid)
  - ✅ .specify/templates/spec-template.md (supports bounded user scenarios and measurable outcomes)
  - ✅ .specify/templates/plan-template.md (supports constitution gates and concrete project structure)
  - ✅ .specify/templates/tasks-template.md (supports story-led implementation and QA tasks)
  - ✅ .specify/templates/checklist-template.md (supports requirement-quality gates)
- Runtime guidance reviewed:
  - ✅ AGENTS.md
  - ✅ CLAUDE.md
- Amendment: made live-browser inspection and four-viewport evidence a mandatory pre-specification,
  pre-plan, pre-architecture, and pre-code gate.
- Follow-up TODOs: none
-->

# ZAKEY v2 Frontend Constitution

## Core Principles

### I. Frontend Approval Gate and Scope Isolation

The first approved delivery MUST be a complete frontend reference build. It MUST include the
customer-facing presentation, local prototype states, interactions, accessibility, responsive
behavior, and visual evidence needed for user review. It MUST NOT include database models,
business migrations, admin features, real authentication, server-side or customer persistence,
real orders, payment execution or provider integration, inventory, APIs, external-provider
integrations, deployment, or production actions. Replaceable browser-local prototype state and
clearly labelled non-integrated payment-choice UI are permitted. Backend
planning and implementation MUST remain a separate future feature and MUST NOT begin before the
user explicitly approves the integrated frontend.

### II. Reference Fidelity and Governed Design System

The live approved reference is the binding visual authority. Every page MUST use one coherent
design system with documented tokens, shared layout components, consistent cards and controls,
and deliberate responsive transformations. Material differences in hierarchy, section order,
density, grid, spacing, typography, imagery, header, hero, or footer MUST be corrected rather
than described as creative freedom. Creative changes MAY be made only when they improve usability
or perceived quality without changing the reference identity.

Codex MUST personally open the live reference in a real browser, discover every accessible screen
and important interaction, capture evidence at 1440px, 1024px, 768px, and 390px, and approve a
written reference inventory before finalizing the specification, plan, component architecture, or
frontend code. The written brief MUST NOT substitute for reference inspection. If the reference
cannot be inspected sufficiently after reasonable retry and diagnosis, work MUST stop with the
exact decision `REFERENCE INSPECTION BLOCKED`; an alternative design MUST NOT be invented.

### III. Arabic-First Accessible Responsive Experience

All customer-facing experiences MUST be Arabic-first, fully RTL, localized for the Egyptian
market, keyboard operable, and usable at 1440px, 1024px, 768px, and 390px. Semantic landmarks,
logical heading order, visible focus, labelled controls, linked Arabic validation messages,
accessible dialogs, drawers, tabs, and accordions, suitable touch targets, sufficient contrast,
alternative text, and reduced-motion support are mandatory. No critical or serious automated
accessibility violation may remain.

### IV. Replaceable Prototype Data and Progressive Enhancement

All catalogue, category, price, specification, review, partner, FAQ, cart, wishlist, checkout,
and account prototype content MUST originate from one clearly isolated development fixture
boundary. Templates and interaction code MUST NOT scatter competing product records or imply that
prototype content is verified production data. Core content and navigation MUST remain useful
without client-side scripting; modular native interaction code MUST enhance the rendered pages
without creating a single-page application or an accidental backend contract.

### V. Evidence-Based Quality Gates

Completion MUST be supported by executable evidence, not source inspection alone. Every required
page and material state MUST receive functional, responsive, accessibility, console, HTML, and
visual review. Screenshots MUST cover all required viewports. Two visual critique passes MUST be
recorded and their material findings fixed. The final production-code, test-code, and documentation
diffs MUST pass their respective guard reviews. Failing checks MUST be fixed or reported as an
exact blocker; tests MUST NOT be weakened and success MUST NOT be fabricated.

## Frontend Technology and Product Constraints

- The implementation MUST use Django template inheritance only as a minimal rendering shell,
  semantic HTML, locally compiled Tailwind CSS, focused custom CSS, and native modular JavaScript.
- The implementation MUST have no CDN runtime dependency and MUST NOT introduce React, Vue,
  Angular, Svelte, Next.js, another SPA architecture, or an unnecessary component framework.
- The visual system MUST be Light Mode only and MUST use the approved ZAKEY colors, Cairo for
  Arabic, Poppins only for suitable Latin content, a 12-column desktop grid, an 8px spacing system,
  governed 12px radii, restrained shadows, intentional whitespace, and purposeful motion.
- The implementation MUST use Egyptian pound presentation, 14% VAT messaging, the canonical 27
  governorates, Egyptian phone validation, and explicitly bounded Greater Cairo/Alexandria service
  messaging. Prototype payment options MUST be labelled as non-integrated UI states.
- Dependencies MUST be limited to those required for the local frontend build and its QA gates.

## Delivery Workflow and Review Gates

1. Inventory and remove superseded local feature artifacts without rewriting history or touching
   remote branches.
2. Establish this constitution, inspect the live reference, capture the required viewport/state
   evidence, and approve the reference inventory.
3. Create, clarify, validate, plan, task, and analyze one active frontend-only feature.
4. Resolve every material cross-artifact finding before implementation.
5. Implement tasks phase by phase and mark a task complete only after its acceptance evidence is
   available.
6. Run functional, responsive, accessibility, HTML, console, screenshot, and two-pass visual QA;
   fix all material findings.
7. Run clean-code, test, and documentation guard passes and repeat affected checks after fixes.
8. Stop for user visual approval. Do not push, open a pull request, merge, rebase, deploy, commit,
   alter remotes, or begin backend work without separate authorization.

## Governance

This constitution is authoritative for Specification 003 and supersedes conflicting workflow,
plan, or task text. Amendments require an explicit user instruction, a documented semantic version
change, an updated Sync Impact Report, and propagation to affected templates and feature artifacts.
Reviewers MUST verify constitution compliance at planning, post-design, pre-implementation, and
final-delivery gates. Any exception MUST name the violated rule, the reason, the smallest bounded
scope, and the condition that removes the exception.

**Version**: 1.1.0 | **Ratified**: 2026-08-01 | **Last Amended**: 2026-08-01
