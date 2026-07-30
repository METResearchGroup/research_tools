# Step 1: Declare toolchain extras and make existing hooks pass

## Remember
- Exact file paths always
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Delegated tasks must be impossible to misread.

## Goal

Install the quality toolchain as optional extras and make the existing Ruff + Pyright pre-commit hooks exit 0 on the current tree before adding new hooks in Step 2.

## Scope

- **Caller:** `uv run pre-commit` / `uv run ruff` / `uv run pyright` as invoked from `/Users/mark/src/work/research_tools/.pre-commit-config.yaml`.
- **Slice:** declare extras → sync → fix Ruff check/format → confirm Pyright clean.
- **Out of scope:** Lizard, codespell, meta hooks, GitHub Actions, LiteLLM bump, SETUP docs (those are Steps 2–3).

## Files

### Inspect

- `/Users/mark/src/work/research_tools/pyproject.toml`
- `/Users/mark/src/work/research_tools/uv.lock`
- `/Users/mark/src/work/research_tools/.pre-commit-config.yaml`
- `/Users/mark/src/work/research_tools/src/research_tools/env.py` (unused `Path` import)
- `/Users/mark/src/work/research_tools/src/research_tools/retry.py` (format drift)
- `/Users/mark/src/work/research_tools/tests/prompting/test_prompt_builder.py` (format drift)
- `/Users/mark/src/work/research_tools/tests/test_anthropic_provider.py` (format drift)
- `/Users/mark/src/work/research_tools/tests/test_llm_service_env_overrides.py` (format drift)

### Allowed to change

- `/Users/mark/src/work/research_tools/pyproject.toml` (optional-dependencies only for quality tools; do not change runtime deps here)
- `/Users/mark/src/work/research_tools/uv.lock` (via `uv lock` / `uv sync`)
- `/Users/mark/src/work/research_tools/src/research_tools/env.py` (remove unused import only)
- `/Users/mark/src/work/research_tools/src/research_tools/retry.py` (Ruff format only)
- `/Users/mark/src/work/research_tools/tests/prompting/test_prompt_builder.py` (Ruff format only)
- `/Users/mark/src/work/research_tools/tests/test_anthropic_provider.py` (Ruff format only)
- `/Users/mark/src/work/research_tools/tests/test_llm_service_env_overrides.py` (Ruff format only)

### Forbidden to change

- `/Users/mark/src/work/research_tools/.pre-commit-config.yaml` (Step 2)
- `/Users/mark/src/work/research_tools/.github/**` (Step 3)
- `/Users/mark/src/work/research_tools/SETUP.md` / `/Users/mark/src/work/research_tools/README.md` (Step 2)
- Runtime dependency pins in `pyproject.toml` (LiteLLM bump is Step 3)
- Any production logic beyond unused-import removal and auto-format

## Contract freeze

1. **Optional extra name:** `dev` (or extend existing `test` only if you deliberately keep a single group — prefer a separate `dev` extra so consumers of `test` stay lean).

2. **Packages that must be installable via `uv sync --extra test --extra dev`:**
   - `ruff`
   - `pyright`
   - `lizard`
   - `codespell`
   - `pre-commit`

3. **Existing hook entries in `.pre-commit-config.yaml` stay as `uv run …` system hooks** for this step; do not rewrite them yet.

4. **Pyright scope:** package under `src/research_tools` and tests under `tests/` must type-check with exit 0. If a `pyrightconfig.json` / `[tool.pyright]` section is required for src-layout resolution, add the minimal config under `/Users/mark/src/work/research_tools/pyproject.toml` or `/Users/mark/src/work/research_tools/pyrightconfig.json` (creating that file is allowed if needed).

## Implementation order

1. Add the `dev` optional-dependencies list to `/Users/mark/src/work/research_tools/pyproject.toml` with the five packages above (pin loosely with `>=` unless the repo already pins tools tightly).
2. Run `uv sync --extra test --extra dev` and confirm the lockfile updates.
3. Fix Ruff:
   - `uv run ruff check --fix src tests`
   - `uv run ruff format src tests`
4. Run `uv run pyright` (or `uv run pyright src tests` if that is what the hook effectively needs). Add minimal pyright config only if resolution fails.
5. Re-run the three existing hook commands manually before Step 2 changes the config.

## Commands (exact; expected outcomes)

```bash
cd /Users/mark/src/work/research_tools
uv sync --extra test --extra dev
# Expected: exit 0; ruff, pyright, lizard, codespell, pre-commit present in .venv

uv run ruff check --fix src tests
# Expected: exit 0; F401 in env.py fixed

uv run ruff format src tests
# Expected: exit 0; the four drifted files reformatted

uv run ruff check src tests
# Expected: exit 0; "All checks passed!"

uv run ruff format --check src tests
# Expected: exit 0; "N files already formatted"

uv run pyright
# Expected: exit 0; 0 errors
# If pyright is missing: fail Step 1 — extras were not wired correctly
```

## Pass / fail

| Must pass | Must fail / must not happen |
| --- | --- |
| `uv sync --extra test --extra dev` exit 0 | Changing LiteLLM or other runtime pins |
| `uv run ruff check src tests` exit 0 | Editing `.pre-commit-config.yaml` |
| `uv run ruff format --check src tests` exit 0 | Adding GitHub Actions |
| `uv run pyright` exit 0 | Leaving unused `Path` import |
| `uv run pytest -q` exit 0 (sanity; format-only changes) | Behavior changes in tests beyond formatting |

## Done when

- `dev` extra installs the five tools.
- Existing Ruff + Pyright commands are green on the full tree.
- No Step 2/3 files were touched.
