# Step 2: Add Lizard, codespell, and meta hooks; document install

## Remember
- Exact file paths always
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Delegated tasks must be impossible to misread.

## Goal

Expand pre-commit so every commit runs Lizard on `src/` + `tests/`, codespell, and standard file-hygiene hooks, all green on the current tree, with install instructions in SETUP.

## Scope

- **Caller:** `pre-commit` on developer commits; later mirrored by CI in Step 3.
- **Slice:** update hook config → verify all hooks green → document install/run.
- **Out of scope:** GitHub Actions workflow, `uv audit`, LiteLLM bump, new product features.

## Files

### Inspect

- `/Users/mark/src/work/research_tools/.pre-commit-config.yaml`
- `/Users/mark/src/work/research_tools/SETUP.md`
- `/Users/mark/src/work/research_tools/README.md` (only if SETUP should be cross-linked)
- `/Users/mark/src/work/research_tools/pyproject.toml` (confirm `dev` extra from Step 1)
- Baseline Lizard: defaults already pass on this tree (`CCN > 15` / length defaults → 0 warnings on `src` + `tests`)

### Allowed to change

- `/Users/mark/src/work/research_tools/.pre-commit-config.yaml`
- `/Users/mark/src/work/research_tools/SETUP.md`
- `/Users/mark/src/work/research_tools/README.md` (one-line pointer to SETUP pre-commit section only if needed)
- `/Users/mark/src/work/research_tools/pyproject.toml` only if codespell needs a tiny `[tool.codespell]` skip list after a real false positive
- Source/test files **only** to fix genuine codespell findings or Lizard threshold violations (prefer fix over whitelist)

### Forbidden to change

- `/Users/mark/src/work/research_tools/.github/**` (Step 3)
- Runtime dependency pins (LiteLLM) (Step 3)
- Plan packet files other than this step’s own edits

## Contract freeze

### Lizard (local system hook via `uv run`)

- **Languages:** Python only (`-l python`).
- **Paths:** `src` and `tests` (both required).
- **Thresholds:** default CCN warning threshold `15` (`-C 15`). Do not loosen with `-i` ignore-warnings.
- **Warnings must fail the hook:** Lizard already exits non-zero when warnings exist; do not add ignore flags.
- **Entry shape:** `uv run lizard src tests -l python -C 15` (equivalent flags OK if documented in the hook `entry`).
- **`pass_filenames`:** `false` (analyze the fixed trees, not the staged subset alone).
- **Types:** Python files trigger the hook (or always-run with `pass_filenames: false` — pick one consistent pattern matching the existing pyright hook).

### codespell

- Prefer the official codespell pre-commit mirror repo (`codespell-project/codespell`) **or** a local `uv run codespell` system hook — choose one and keep it consistent with how Ruff is invoked (prefer `uv run codespell` if that keeps one toolchain).
- Targets: repository text that developers edit — at minimum `src/`, `tests/`, `README.md`, `SETUP.md`, `CHANGELOG.md`, `pyproject.toml`. Exclude `.venv`, lockfile binary noise, and `uv.lock` if codespell complains about hashes/noise.
- Must exit 0 on the current tree (baseline already clean for the paths listed in the plan discovery run).

### Meta hooks (`pre-commit/pre-commit-hooks`)

Include at least:

- `trailing-whitespace`
- `end-of-file-fixer`
- `check-yaml`
- `check-toml`
- `check-merge-conflict`
- `check-added-large-files`

Pin a current stable `rev` of `pre-commit/pre-commit-hooks` (do not leave `rev: master`).

### Cleanup

- Remove `exclude: ^ai_tools/` from the Ruff format hook — that path does not exist in this repository.

### Docs

In `/Users/mark/src/work/research_tools/SETUP.md`, add a short section after install that states:

1. `uv sync --extra test --extra dev`
2. `uv run pre-commit install`
3. `uv run pre-commit run --all-files` (optional full check)

## Implementation order

1. Edit `.pre-commit-config.yaml`: drop `ai_tools` exclude; add Lizard; add codespell; add meta hooks repo.
2. Run `uv run pre-commit run --all-files`. Fix any auto-fixable meta-hook issues (EOF/whitespace) by accepting the hook’s edits.
3. If Lizard or codespell fails, fix the offending source/docs (or add a minimal codespell skip only for a documented false positive).
4. Update SETUP.md with the three commands above.
5. Re-run full pre-commit until exit 0.

## Commands (exact; expected outcomes)

```bash
cd /Users/mark/src/work/research_tools
uv sync --extra test --extra dev

uv run lizard src tests -l python -C 15
# Expected: exit 0; "No thresholds exceeded ..." / Warning cnt 0

uv run codespell src tests README.md SETUP.md CHANGELOG.md pyproject.toml
# Expected: exit 0; no output (or only skip notices)

uv run pre-commit install
# Expected: exit 0; "pre-commit installed at .git/hooks/pre-commit"

uv run pre-commit run --all-files
# Expected: exit 0; every hook reports Passed (first run may modify EOF/whitespace — re-run until clean)
```

## Pass / fail

| Must pass | Must fail / must not happen |
| --- | --- |
| `uv run lizard src tests -l python -C 15` exit 0 | Lizard scoped to only `src/` |
| codespell exit 0 on agreed paths | Leaving `exclude: ^ai_tools/` |
| `uv run pre-commit run --all-files` exit 0 | Adding GitHub Actions in this step |
| SETUP documents sync + `pre-commit install` | Using `-i` to ignore Lizard warnings |
| Meta hooks present and pinned by tag/sha | Ignoring codespell by deleting the hook |

## Done when

- Pre-commit suite includes Ruff, Pyright, Lizard (`src`+`tests`), codespell, and meta hooks — all green.
- SETUP tells a new developer how to install hooks.
- CI files still absent (Step 3).
