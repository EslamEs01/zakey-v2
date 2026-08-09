# Dependency vulnerability audit — T-1706 (NFR-006)

**Scanner**: `pip-audit` 2.10.1, run via `uvx` so the tool's own dependencies
never enter the project environment.

**Target**: the resolved lockfile, exported with
`uv export --format requirements-txt --no-hashes --all-extras`.

## A correction worth recording

The first run was `uvx pip-audit` with no arguments. It reported
**"No known vulnerabilities found"** and scanned **29 packages**.

That result was wrong, and the giveaway was the package count: ZAKEY resolves to
25 packages, and `pip-audit` with no target audits *the environment it is
running in* — which under `uvx` is pip-audit's own sandbox, not this project.
A clean bill of health from the wrong environment is worse than no scan, because
it closes the question.

The corrected invocation targets the exported requirements explicitly:

```bash
uv export --format requirements-txt --no-hashes --all-extras > requirements-audit.txt
uvx pip-audit -r requirements-audit.txt --progress-spinner=off -f json
```

Anyone re-running this check must pass `-r`. A bare `uvx pip-audit` will pass
while telling you nothing.

## Findings (before remediation)

`scanned=25  vulnerable_packages=2  advisories=26`

| Package | Version | Advisories | Fixed in |
|---|---|---|---|
| Pillow | 11.3.0 | 25 | 12.3.0 |
| pytest | 8.4.2 | 1 (PYSEC-2026-1845) | 9.0.3 |

### Pillow — the one that matters

25 advisories, and the exposure is direct rather than theoretical. `T-1702`
routes **attacker-controlled uploads** through `PIL.Image.open()` and
`Image.verify()` in `apps/core/uploads.py`, and the admin re-encodes them. A
memory-safety bug in Pillow's decoders is reachable by any staff member who can
be persuaded to upload a file, which is precisely the threat T-08 describes.

Both pins blocked the fix:

```toml
"Pillow>=11,<12"   # 12.3.0 excluded
"pytest>=8,<9"     # 9.0.3 excluded
```

### pytest

Development-only; it never runs in production. Still upgraded, because a
test-runner vulnerability is a supply-chain foothold in CI.

## Remediation

`pyproject.toml` constraints widened to admit the fixed releases, then
`uv lock` re-resolved and the full suite re-run to prove the upgrade broke
nothing. See the run recorded alongside this file.

## Re-running

```bash
uv export --format requirements-txt --no-hashes --all-extras > /tmp/req.txt
uvx pip-audit -r /tmp/req.txt --progress-spinner=off
```

Exit code 0 and "No known vulnerabilities found" over **25** packages is the
passing condition. A different package count means the wrong target was scanned.
