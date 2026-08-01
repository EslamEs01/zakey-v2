# Requirements Traceability

**Feature**: `003-zakey-frontend-reference-build`
**Matrix authority**: [contracts/qa-matrix.json](contracts/qa-matrix.json) expands 56 named states
across four widths into 224 required evidence cells.

## Functional requirements to tasks and evidence

| Requirements | Primary implementation tasks | Verification tasks/evidence |
|---|---|---|
| FR-001–FR-009, FR-002A shared frame/authority/states | T012–T020 | T069–T071, T077–T079 |
| FR-010–FR-018 Home | T021–T024 | T021–T022, T025, Home/newsletter matrix states |
| FR-019–FR-026, FR-026A discovery | T026–T032 | T026–T027, T033, catalogue matrix states |
| FR-027–FR-034 Product | T034–T040 | T034–T035, T041, product matrix states |
| FR-035–FR-040 Wishlist/Cart | T042–T048 | T042, T049, wishlist/cart matrix states |
| FR-041–FR-048 Checkout | T050–T056 | T050–T051, T057, checkout matrix states |
| FR-049–FR-055 Account/About/Contact/Errors | T058–T065 | T058–T059, T066, account/contact/error matrix states |
| FR-056–FR-064 localisation/a11y/responsive | T009, T013–T020, T053–T054, T067–T073 | T067–T079 and localisation assertions |
| FR-065–FR-067 fixtures | T009–T012, T019 | T010–T011, T042, SC-015 validation |
| FR-068–FR-071 evidence | T067–T084 | 224-cell inventory, QA reports and two visual passes |
| FR-072 progressive enhancement | T012, T014–T020, T029 | T033, T072 and `qa/progressive-enhancement.md` |

## User stories to independent evidence

| Story | Task phase | Independent evidence |
|---|---|---|
| US1 Discover ZAKEY | T021–T025 | Home order/render tests, browser journey, four-width captures |
| US2 Browse/search/filter | T026–T033 | GET/parity tests, drawer/filter/sort/pagination/zero-state journeys |
| US3 Product evaluation | T034–T041 | Product route and complete gallery/tab/cart/wishlist interaction tests |
| US4 Wishlist/cart | T042–T049 | state/storage/totals/coupon tests and empty/populated captures |
| US5 Checkout | T050–T057 | Egypt validation/eligibility/step/no-submission tests and captures |
| US6 Support/account/errors | T058–T066 | route/tab/form/recovery tests and state captures |
| US7 Accessible responsive use | T067–T073 | axe, keyboard, no-JS, integrity and manual accessibility reports |

## Success criteria to final evidence

| Success criteria | Evidence destination |
|---|---|
| SC-001–SC-008 journeys/controls/a11y behavior | Django and Playwright command results; `qa/interaction-matrix.md` |
| SC-009 axe | `qa/accessibility-results.md` with critical=0, serious=0 |
| SC-010 HTML/console | `qa/final-verification-report.md` and per-cell integrity records |
| SC-011 screenshot completeness | `qa/screenshot-inventory.md`: 224 required cells, no blank cell |
| SC-012 two visual passes | `qa/visual-comparison-findings.md` and recapture inventory |
| SC-013–SC-015 localisation/fixture consistency | Django fixture tests and checkout/catalogue browser tests |
| SC-016 guards | final guard sections in `qa/final-verification-report.md` |
| SC-017 no-JavaScript | `qa/progressive-enhancement.md`, 10 shell routes × four widths (40 cases), plus Django GET catalogue/search tests |

## Reference authority trace

- Home reference order and measurements → FR-003/010/011 → T023/T025 → visual pass one.
- Shared header/footer/navigation → FR-002/002A → T014–T016/T020 → route and keyboard matrix.
- Shop sidebar/drawer/grids → FR-019–026A → T028–T033 → catalogue states.
- Product gallery/tabs/related grid → FR-027–034 → T036–T041 → product states.
- Cart/checkout/account responsive compositions → FR-035–050 → T043–T061 → commerce/account states.
- Source defects and intentional corrections → FR-009/060–064 → T031/T049/T071 → visual/a11y reports.

## Boundary trace

The exclusion contract maps to T001–T091: no task creates models, migrations, admin, APIs,
authentication, server persistence, provider integrations, durable orders or production actions.
T088 explicitly audits the integrated tree for boundary violations; T091 enforces the backend stop.
