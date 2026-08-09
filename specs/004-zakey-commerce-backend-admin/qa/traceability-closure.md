# T-1806 closure record — how the matrix was completed

`traceability.md` is generated, so this is the part that cannot be regenerated:
what was done to the repository to make the generator's output true.

## 1. The starting position

```
uv run python scripts/traceability.py --check
122 functional requirements · 122 with a task claim · 53 with test evidence · 68 problems
```

Every problem was of the form `FR-xxx: no test proves it`. The matrix header
still claimed **76**; that number was stale, written before the last batch of
work landed. The authoritative figure is whatever `--check` prints, which is why
nothing here quotes a number that was not produced by running it.

## 2. How the 68 were closed

The mechanism is unchanged and worth restating, because it is what makes a
mapping honest or dishonest: `scripts/traceability.py` AST-walks the test tree
and attributes a requirement to the **exact node whose docstring names it**.
Closing a gap therefore means naming the requirement in the docstring of a test
that *actually asserts it*, or writing that test where none exists.

Eight agents worked disjoint requirement ranges with **exclusive file
ownership**, so no two could edit the same file. Each was given the literal spec
text of its requirements and one rule above all others: *a false mapping is
worse than an open gap*. Every mapping was then reviewed here, individually.

15 new test files were written. Roughly 540 tests were added — the suite went
from 1,363 to **1,902 collected**.

### What "honest" turned out to mean in practice

The requirements that had gone unmapped longest were mostly **negative or
absence requirements**, which is exactly why: they cannot be proved by exercising
a feature. The mappings that closed them do real work —

- **FR-071 / FR-079** (no payment provider integration exists) — an AST import
  scan across every shipped `.py` for 22 gateway SDK module names, plus checks
  that no such package is declared, no provider endpoint appears in source, and
  no provider credential is configured.
- **FR-099** (presentational labels stay in templates) — proved *negatively*: the
  fixed labels still render with the content tables **empty**, which they could
  not do if a database row supplied them.
- **FR-133** (business rules out of JavaScript) — comment-stripped scan of the
  shipped bundle for money identifiers, currency formatting and commerce
  constants, plus freezing the client payload's key set so the browser is not
  even handed the inputs a pricing rule would need.
- **FR-105 / FR-114** (ledgers read-only, audit immutable) — asserted against a
  **superuser**, at both the model layer and over HTTP. A ledger that is
  read-only only for the under-privileged is not read-only.
- **FR-131** (routes resolve identically) — the pre-existing suite proved route
  *names* still reverse, which renaming `path("shop/")` to `path("store/")`
  would have survived. The URLs are now frozen literally.
- **FR-136** (usable without JavaScript) — the previous spec asserted a 200, an
  `h1` and the noscript note, all of which the prototype's empty shells would
  also have passed. It now drives a customer through add → see total → change
  quantity → remove → sort → checkout with `javaScriptEnabled: false`.

## 3. Two fixes to the generator itself

**Narrowest claim wins.** A module docstring naming several requirements gave
*every* test in the file to *each* of them. `tests/security/test_admin_readonly.py`
reported 26 tests for FR-105, FR-107, FR-108, FR-112 and FR-114 alike, and the
sampled evidence column could cite a bulk-action test as proof of a read-only
rule. A module-level claim now applies only to requirements that no class or
function in that same file claims for itself.

| requirement | before | after |
|---|---|---|
| FR-105 | 26 | 7 |
| FR-107 | 26 | 3 |
| FR-114 | 26 | 8 |

**No requirement lost its mapping** — one claimed narrowly keeps its own nodes,
one claimed only at module level still covers the file.

**Node IDs are now verified against pytest, not just the AST.**
`scripts/verify_traceability_nodes.py` asks pytest itself, via `--collect-only`,
whether every mapped node is *collectible*. A method on a class pytest does not
collect, or a file outside `python_files`, looks perfectly valid to an AST walk
and never runs. Building it surfaced a trap worth recording: node IDs need
**exactly one** `-q` — none prints a tree, two collapses to per-file counts, and
`pyproject.toml`'s `addopts` already supplies one. The first version silently
compared against an empty set and declared all 661 mappings broken.

`scripts/audit_module_level_claims.py` reports module-level claims and whether
narrower ones already cover them.

## 4. What was found on the way

Five things where the specification and the repository disagreed — recorded in
**`qa/spec-divergences.md`**, not silently absorbed:

| # | subject | state |
|---|---|---|
| 1 | FR-086 — coupon rejection message | resolved in code |
| 2 | FR-132 — localStorage migration adapter | resolved by supersession |
| 3 | FR-025 — release on payment failure | ⚠️ open — product decision |
| 4 | `base.html` no-JS notice now understates the product | ⚠️ open — belongs to T-1901 |
| 5 | FR-075 — refund cap has no database constraint | ⚠️ open — schema change |

Three are deliberately left open. Two of those (25 and 75) are cases where an
agent could have closed its gap by writing a test that names the requirement and
proves something adjacent, and refused to. That refusal is the point of the
exercise.

**#5 deserves attention beyond this task.** The repository's stated philosophy
is that load-bearing invariants are enforced by a database constraint rather
than by convention, and `reserved <= on_hand` really is. The refund cap — the
money-losing invariant — is enforced only by the service layer under a row lock.

## 5. Verification

Four gates, all run after the last edit landed:

| gate | result |
|---|---|
| `scripts/traceability.py --check` | **exit 0 · 0 problems** |
| two consecutive runs from equivalent state | **byte-identical** — md5 `18f0c205be6937fbbe90f18b69247139`, both exit 0 |
| `scripts/verify_traceability_nodes.py` | **777 mapped nodes, every one collectible** by `pytest --collect-only`, plus 1 Playwright spec |
| full Python suite (1,902 tests) | **1,900 pass**; 2 wall-clock tests are load-sensitive — see below |

### The two failures are load-sensitive, and that is stated rather than hidden

Two tests failed the full run, both of them wall-clock assertions:

| test | observed |
|---|---|
| `tests/performance/test_performance.py::TestCataloguePerformance::test_home_p95` | 404 ms against a 300 ms p95 budget |
| `tests/security/test_login_rate_limit.py::test_login_form_failure_wall_time_is_equalised` | 0.156 s spread against a 0.1 s tolerance |

Both are **pre-existing tests that this session did not touch** — `git status`
on both paths is empty — and both **pass when run in isolation** (26 tests, all
green). The machine is shared: load average was 8–15 during the full run, with
unrelated projects' servers and test suites resident.

So the honest statement is not "the suite is green". It is: **every assertion
about behaviour passes; two assertions about elapsed time fail when the machine
is busy and pass when it is not.** Neither has anything to do with traceability,
and neither is part of `npm run qa`, which runs Playwright rather than pytest.

Worth someone's attention independently: a p95 budget and a timing-equalisation
tolerance that flake under load will flake in CI too. They want either a quieter
runner or a tolerance derived from a measured baseline rather than a constant.

Recorded rather than quietly re-run until green, because "we re-ran it and it
passed" is exactly how a real intermittent failure gets buried.

### A note for anyone repeating this with parallel agents

Every agent independently hit the same wall: `pytest-django` derives one test
database name from `DATABASE_URL`, so N concurrent agents fight over
`test_zakey` and produce `DuplicateDatabase` / "being accessed by other users"
errors that look exactly like test failures and are not. Each agent worked
around it by choosing a private `DATABASE_URL`, and two of them independently
picked the *same* private name. If you fan out like this, assign the database
names up front along with the file ownership.
