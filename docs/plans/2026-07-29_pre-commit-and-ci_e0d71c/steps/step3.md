# Step 3: Add GitHub Actions CI with pytest and uv audit

## Remember
- Exact file paths always
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Delegated tasks must be impossible to misread.

## Goal

Add a CI workflow on PRs and pushes to `main` that runs the same pre-commit suite, pytest, and `uv audit`, all exiting 0. Resolve current LiteLLM advisories by bumping the pin so audit is clean without ignore lists.

## Scope

- **Caller:** GitHub Actions on `pull_request` and `push` to `main`; local dry-run of the same commands before merge.
- **Slice:** bump LiteLLM → confirm audit clean → add workflow → document CI expectation briefly if SETUP already has a quality section.
- **Out of scope:** coverage gates, bandit, secrets scanners, multi-OS matrix (single `ubuntu-latest` + Python 3.12 is enough).

## Files

### Inspect

- `/Users/mark/src/work/research_tools/pyproject.toml` (`litellm==1.81.0` today)
- `/Users/mark/src/work/research_tools/uv.lock`
- `/Users/mark/src/work/research_tools/.pre-commit-config.yaml` (must already be green from Step 2)
- `/Users/mark/src/work/research_tools/SETUP.md`
- Current audit baseline: `uv audit` fails on LiteLLM 1.81.0 with many GHSA/PYSEC findings; highest “Fixed in” among reported issues is **1.84.0**.

### Allowed to change

- Create `/Users/mark/src/work/research_tools/.github/workflows/ci.yml` (name may be `ci.yml` or `quality.yml`; one workflow file)
- `/Users/mark/src/work/research_tools/pyproject.toml` (LiteLLM pin bump only among runtime deps)
- `/Users/mark/src/work/research_tools/uv.lock` (via `uv lock` after the bump)
- `/Users/mark/src/work/research_tools/SETUP.md` (optional one-sentence note that CI runs pre-commit, pytest, and `uv audit`)
- `/Users/mark/src/work/research_tools/CHANGELOG.md` if the repo tracks dependency bumps there
- Test/source files **only** if the LiteLLM bump breaks imports/APIs used by this package (fix minimally; do not expand features)

### Forbidden to change

- Softening audit with `--ignore` / `--ignore-until-fixed` as the default solution (allowed only if a finding has no fix version after bumping to the latest available LiteLLM — then document the exact ID and reason in SETUP; prefer bump first)
- Dropping pytest or pre-commit from CI
- Changing Lizard thresholds to make CI green
- Unrelated refactors

## Contract freeze

### LiteLLM bump

1. Raise the pin from `1.81.0` to a version **≥ 1.84.0** that clears `uv audit` (verify after lock; if 1.84.0 still reports findings, keep bumping to the newest fix version that clears the audit).
2. Re-run `uv run pytest -q` after the bump; fix any API breakages narrowly.
3. Do not leave `uv audit` red on `main`.

### Workflow jobs / steps

Single job is fine (or split audit if desired). Required steps in order:

1. Checkout
2. Install `uv` (official `astral-sh/setup-uv` action)
3. `uv sync --extra test --extra dev --frozen` (or `--locked` if that is the project’s lock discipline)
4. `uv run pre-commit run --all-files`
5. `uv run pytest -q`
6. `uv audit` (pass `--preview-features audit` if required by the installed uv version to avoid experimental warnings becoming noise; exit code must still be non-zero on findings)

### Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
```

### Runner

- `ubuntu-latest`
- Python 3.12 (match `requires-python = ">=3.12"`)

## Implementation order

1. Bump LiteLLM in `pyproject.toml`; `uv lock` / `uv sync --extra test --extra dev`.
2. Run `uv audit` until exit 0.
3. Run `uv run pytest -q` until exit 0.
4. Create `.github/workflows/ci.yml` with the steps above.
5. Locally dry-run the CI command sequence.
6. Optionally note in SETUP that PRs must pass these checks.

## Commands (exact; expected outcomes)

```bash
cd /Users/mark/src/work/research_tools

# After editing the LiteLLM pin in pyproject.toml:
uv lock
uv sync --extra test --extra dev
# Expected: exit 0; lockfile reflects new litellm version

uv audit
# Expected: exit 0; "Found 0 known vulnerabilities ..." (wording may vary)
# Must NOT exit 1 with LiteLLM advisories remaining

uv run pytest -q
# Expected: exit 0

uv run pre-commit run --all-files
# Expected: exit 0

# Local CI dry-run (same order as the workflow):
uv sync --extra test --extra dev --frozen
uv run pre-commit run --all-files
uv run pytest -q
uv audit
# Expected: all exit 0
```

## Pass / fail

| Must pass | Must fail / must not happen |
| --- | --- |
| `uv audit` exit 0 after LiteLLM bump | Shipping CI with failing audit on 1.81.0 |
| `uv run pytest -q` exit 0 | Ignoring vulns without documenting why |
| `uv run pre-commit run --all-files` exit 0 | Workflow missing pytest or audit |
| Workflow exists under `.github/workflows/` and triggers on PR + `main` | Multi-OS matrix scope creep |
| Workflow uses `uv` + extras including `dev` | Pinning Python below 3.12 |

## Done when

- CI config is committed and locally dry-run green.
- `uv audit` is clean after the LiteLLM bump.
- PRs to `main` will run pre-commit, pytest, and audit as merge gates (once the workflow is on the default branch).
