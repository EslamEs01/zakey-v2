# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]  
**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]  
**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]  
**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]  
**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]
**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]  
**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]  
**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]  
**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: This check MUST pass before Phase 0 research begins, and MUST be re-run and re-recorded
after Phase 1 design. A principle is never marked Pass without cited evidence — name the plan
section, artifact, or decision that carries the compliance. "Will comply" is not evidence.*

<!--
  ACTION REQUIRED: Complete BOTH columns for every principle. Replace the Status placeholder
  with Pass / Violation / Not applicable. A "Not applicable" entry MUST state why.
  Any Violation is a blocker: record it in Blocking Violations below and either resolve it or
  obtain a documented, user-approved exception before proceeding. Complexity that conflicts
  with a principle MUST be justified in Complexity Tracking.
-->

### Initial gate (before Phase 0)

| # | Principle / gate area | Status | Evidence (section, artifact, or decision) |
| --- | --- | --- | --- |
| I | Reference-led visual fidelity — named pages, widths, acceptance threshold, verification method; reference defects corrected not reproduced | | |
| II | Design-token authority — one centralized token source; ratified values matched exactly; no competing colours, scales, spacing, radii, shadows, or breakpoints | | |
| III | Approved technical foundation — every dependency assessed for maintenance cost, security exposure, runtime performance, and bundle size; no prohibited technology; no runtime third-party origin | | |
| IV | Architecture boundaries — clean-room; reusable components with no cross-page duplication; focused modules; no single oversized CSS/JS file | | |
| IV.7–IV.8 | Shared data authority — exactly one documented fixture/service/repository/adapter for temporary data; no template hardcodes a duplicated record | | |
| IV.9 | Localization and RTL readiness — externalized strings, direction-aware layout primitives, no LTR-only geometry | | |
| V | Content and asset truth — sources documented; no invented claims; asset manifest with ownership and licensing | | |
| VI | Functional completeness — every control has behavior; no dead controls; no `href="#"`; no fake success; named route lookups; one shared totalling routine; no prohibited payment data | | |
| VII | Responsive behavior — a deliberate layout decision per surface at every ratified width; programmatic overflow assertion planned | | |
| VIII | Accessibility — WCAG 2.2 AA targets; BOTH automated checks and a manual keyboard pass planned | | |
| IX | Performance budgets — page weight, JavaScript payload, and layout stability set before implementation, each with a measurement method | | |
| X | Security and data safety — secrets handling, env validation, CSRF, server-side validation, escaping, least privilege, log hygiene | | |
| XI | Specification-first — no requirement silently redefined; material ambiguity resolved; out-of-scope boundary respected | | |
| XII | Test strategy — the applicable verification set named, with each exclusion justified | | |
| XIII | Visual QA — screenshot capture AND inspection planned at the approved widths; two critique passes for major UI work; cross-page component comparison | | |
| XIV | Code quality — naming, cohesion, no duplicated business logic, narrow exception handling, no debug residue, reviewed migrations; guard skills scheduled | | |
| XV | Git safety — branch strategy; no unauthorized Git operation; ignore policy covers generated artifacts; unrelated user work untouched | | |
| XVI | Claude governance — ownership named; delegation bounded with explicit owners; no concurrent edits to shared surfaces | | |
| XVII | LeanCtx and context discipline — targeted exploration; decisions and evidence written into artifacts, not left in conversation | | |
| — | Implementation boundaries — what this feature will NOT build, and which future feature owns it | | |
| XVIII | Definition of Done — all fifteen conditions reachable by the planned work | | |

### Post-design re-check (after Phase 1)

<!--
  Re-run the same table after data model, contracts, and design decisions exist. Design work
  frequently introduces violations that the initial gate could not see.
-->

| # | Principle / gate area | Status | Evidence |
| --- | --- | --- | --- |
| | | | |

### Blocking Violations

<!--
  MUST be empty before Phase 0 research proceeds. Any entry here stops planning until it is
  resolved or an explicit, user-approved, documented exception exists (Governance > Exceptions).
-->

| Violation | Principle | Why it blocks | Resolution or approved exception |
| --- | --- | --- | --- |
| | | | |

### Dependency Assessment

<!--
  Principle III.4 — every NEW dependency requires this record. A dependency added without it
  MUST be removed or retroactively documented before acceptance.
-->

| Dependency | Purpose | Maintenance cost | Security exposure | Runtime performance | Bundle-size impact |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
