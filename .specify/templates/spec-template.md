# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`
**Feature Number**: `[###]`
**Created**: [DATE]
**Status**: Draft
**Constitution**: [constitution name and version in force]
**Input**: User description: "$ARGUMENTS"

<!--
  SECTION APPLICABILITY
  =====================
  Sections marked *(mandatory)* are required for every feature.
  Sections marked *(mandatory for UI work)* are required whenever the feature renders a
  user interface; for a non-UI feature, replace the section body with one line stating
  it does not apply and why. Do NOT delete a mandatory heading and do NOT leave "N/A"
  without a reason — Constitution Principle XI requires stated applicability.

  The Specification gate (Development Workflow > Gate Matrix) will not pass without:
    - an explicit Out of Scope section (XI.9),
    - measurable acceptance criteria (XII.1),
    - a UI inventory for UI work (XIII.1),
    - performance budgets where relevant (IX.7),
    - a stated reference-fidelity verification method where a visual reference exists (I.6).
-->

## 1. Purpose and Product Outcome *(mandatory)*

<!--
  State WHAT outcome this feature delivers and WHY, in user terms. Name what a user can do
  when it ships that they could not before. State plainly where this feature stops and which
  future feature owns what lies beyond that boundary.
-->

## 2. Authoritative Sources and Evidence *(mandatory)*

<!--
  Principle I and Principle V. Record every source treated as authoritative, how it was
  inspected, on what date, and what was observed. Distinguish visual authority from content
  authority. Where two sources conflict, record the conflict and its resolution explicitly.
  Where an authoritative source contains a defect, record the defect and the required
  correction — a defect must never be reproduced for the sake of similarity (I.4).
  Claims with no traceable source MUST be removed, not softened.
-->

| Source | Method of inspection | Date | Result |
| --- | --- | --- | --- |
| | | | |

## 3. Clarifications

<!--
  Populated by /speckit-clarify. Record one bullet per accepted answer under a dated session
  heading. A material ambiguity (XI.3) MUST be resolved here before planning.
-->

### Session [DATE]

- Q: [question] → A: [answer]

## 4. User Scenarios & Testing *(mandatory)*

<!--
  Prioritize as user journeys (P1, P2, P3…). Each story MUST be independently testable and
  independently valuable — implementing only P1 must still yield a usable increment.
-->

### User Story 1 - [Brief Title] (Priority: P1)

[The journey in plain language]

**Why this priority**: [value and ordering rationale]

**Independent Test**: [how this story is verified on its own]

**Acceptance Scenarios**:

1. **Given** [initial state], **When** [action], **Then** [observable outcome]

---

[Add further user stories with assigned priorities]

### Edge Cases *(mandatory)*

<!--
  Boundary conditions, negative flows, concurrency, stale state, expiry, degraded mode,
  and failure handling. Each edge case states the expected behavior, not just the trigger.
-->

## 5. Page Inventory *(mandatory for UI work)*

<!--
  Principle XIII.1. Evaluate every candidate surface and mark it In scope / Deferred /
  Excluded. A deferred surface MUST name the future specification that owns it. Do not
  invent a surface to lengthen the list.
-->

| # | Surface | Decision | Basis / owning future specification |
| --- | --- | --- | --- |
| | | | |

## 6. Shared Component Inventory *(mandatory for UI work)*

<!--
  Principles IV.5 and XIII.1. Every component family that appears in the interface, defined
  once and reused. Each family MUST list its applicable states.
-->

| # | Family | Purpose | States |
| --- | --- | --- | --- |
| | | | |

## 7. Interaction and Control Inventory *(mandatory for UI work)*

<!--
  Principle VI.1–VI.3. Every visible control, its trigger, and its defined behavior. A control
  with no defined behavior MUST be removed rather than rendered. `href="#"` is forbidden.
-->

| Control | Trigger | Defined behavior |
| --- | --- | --- |
| | | |

## 8. Responsive-State Inventory *(mandatory for UI work)*

<!--
  Principle VII. A deliberate layout decision per surface at every ratified verification
  width. Stacking desktop columns is not a layout decision.
-->

| Surface | [width 1] | [width 2] | [width 3] | [width 4] |
| --- | --- | --- | --- | --- |
| | | | | |

## 9. Loading, Empty, Error, Disabled, and Success States *(mandatory for UI work)*

<!--
  Principle VI.7. Every reachable state, intentionally designed. A success state MUST NOT
  appear unless the underlying operation actually succeeded (VI.4).
-->

| Surface | Loading | Empty | Error | Disabled | Success |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 10. Content and Asset Integrity *(mandatory)*

<!--
  Principle V. Enumerate what may and may not be shown. Invented awards, certifications,
  partnerships, customer numbers, reviews, ratings, specifications, warranties, delivery
  promises, media coverage, trust badges, prices, and stock figures are forbidden. Internal
  development terminology must not reach any user-visible surface.
-->

## 11. Reference-Fidelity Requirements *(mandatory for UI work with a visual reference)*

<!--
  Principle I.6 — this section MUST name the pages compared, the widths compared at, the
  acceptance threshold, and how the comparison is reviewed. Record every intended deviation
  and its justification. Reference defects are corrected, never reproduced (I.4).
-->

## 12. Accessibility Requirements *(mandatory for UI work)*

<!--
  Principle VIII. Target WCAG 2.2 AA where applicable. Every item must be measurable.
  Verification requires BOTH automated checks and a manual keyboard pass (VIII.5, VIII.6).
-->

## 13. Performance Budgets *(mandatory where the feature affects delivered pages or assets)*

<!--
  Principle IX.7 — budgets are set BEFORE implementation. At minimum a page-weight budget,
  a JavaScript-payload budget, and a layout-stability target, each with a stated measurement
  method. A budget must never be met by weakening accessibility, content, or usability.
-->

| Budget | Target | Measured how |
| --- | --- | --- |
| | | |

## 14. Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: [Testable capability. One requirement per bullet, uniquely identified.]

<!--
  Mark a genuinely unresolvable ambiguity as [NEEDS CLARIFICATION: specific question].
  Maximum 3 markers; prioritize by scope > security/privacy > user experience > detail.
-->

### Non-Functional Requirements

- **NFR-001**: [Measurable quality attribute with its verification method.]

### Key Entities *(include if the feature involves data)*

- **[Entity]**: [what it represents, its attributes and relationships, without implementation detail]

## 15. Success Criteria *(mandatory)*

<!--
  Measurable, technology-agnostic, user- or business-facing, and verifiable without knowing
  the implementation.
-->

- **SC-001**: [Measurable outcome]

## 16. Assumptions *(mandatory)*

<!--
  Every reasonable default chosen where the input was silent. Convert relative dates to
  absolute ones.
-->

## 17. Dependencies *(mandatory)*

<!--
  Upstream artifacts, verified content, assets, approvals, and external services this feature
  requires. State what is blocked if a dependency is unavailable.
-->

## 18. Repository Readiness Preconditions *(mandatory)*

<!--
  Verified repository, governance, or tooling conditions that must hold before this feature
  can be planned or implemented. These are readiness findings, NOT product requirements —
  do not convert them into functional requirements. Record verification evidence and the
  stage each one blocks.
-->

| # | Finding | Verified | Severity | Must be resolved before |
| --- | --- | --- | --- | --- |
| | | | | |

## 19. Explicit Out of Scope *(mandatory)*

<!--
  Principle XI.9. Every deferred capability with the future specification that owns it.
  Principle VI.2 means none of these may render a control in the accepted interface.
-->

| Capability | Owning future specification |
| --- | --- |
| | |

## 20. Constitution Compliance *(mandatory)*

<!--
  State, per principle, how this specification complies — citing the requirement, criterion,
  or section that carries the compliance. A principle that does not apply MUST say so and why.
-->

| Principle | How this specification complies |
| --- | --- |
| | |

## 21. Requirement-to-Success-Criterion Traceability *(mandatory)*

<!--
  Principle XI.5 and XVIII.2. Every functional and non-functional requirement maps to at
  least one success criterion or acceptance scenario. Zero unmapped requirements.
-->

| Requirements | Mapped to |
| --- | --- |
| | |

**Coverage**: [N] functional requirements and [N] non-functional requirements — all mapped.
[N] success criteria, all reachable from at least one requirement.
