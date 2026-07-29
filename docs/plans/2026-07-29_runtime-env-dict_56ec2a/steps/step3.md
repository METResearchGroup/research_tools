# Step 3: Document usage and verify

## Remember
- Exact file paths always
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Delegated tasks must be impossible to misread.

## Goal

Document the per-call credential dict on the public structured-completion APIs and confirm the full suite is green for both process-env and override paths.

## Scope

- **Caller:** documentation readers following `/Users/mark/src/work/research_tools/SETUP.md` and `/Users/mark/src/work/research_tools/README.md`.
- **Slice:** add a short usage example + note which keys are allowed; re-run full tests; no new features.
- **Out of scope:** constructor/DI env injection; Bedrock env overrides; changelog/release tagging unless requested separately.

## Files

### Inspect

- `/Users/mark/src/work/research_tools/SETUP.md` (sections “Environment variables” and “Basic usage”)
- `/Users/mark/src/work/research_tools/README.md` (Quick start / env sentence)
- `/Users/mark/src/work/research_tools/src/research_tools/llm_service.py` (final public signatures for accurate docs)
- `/Users/mark/src/work/research_tools/src/research_tools/env.py` (`ENV_VAR_TYPES` / allowed keys)

### Allowed to change

- `/Users/mark/src/work/research_tools/SETUP.md`
- `/Users/mark/src/work/research_tools/README.md`

### Forbidden to change

- `/Users/mark/src/work/research_tools/src/research_tools/**` (unless a doc-driven typo in a docstring is found; prefer leaving code alone)
- `/Users/mark/src/work/research_tools/tests/**`
- Plan files under `/Users/mark/src/work/research_tools/docs/plans/**` except this step’s own edits if needed

## Doc requirements (exact content intent)

1. In `SETUP.md` § Environment variables: state that the same three API-key names may be passed per call via `env={...}` on `structured_completion` / `structured_batch_completion`, and that dict values override process env for that call only. Unknown keys are rejected. Bedrock still uses the AWS credential chain (not these API-key vars).

2. In `SETUP.md` § Basic usage: add a second example after the existing one:

```python
result = service.structured_completion(
    messages=[{"role": "user", "content": "Return a label for this text."}],
    response_model=LabelResponse,
    model="gpt-5.4-nano",
    env={"OPENAI_API_KEY": "..."},
)
```

3. In `README.md`: one sentence noting optional per-call `env` for API keys, linking to `SETUP.md` for detail. Do not expand the quick-start block into a second full example unless it stays under ~15 lines total for that section.

## Verification

```bash
cd /Users/mark/src/work/research_tools
uv run pytest -q
```

**Expected output:** all tests passed (exit code 0). Exact pass count may vary with suite size; zero failures required.

Manual sanity check (optional, no network required if mocked in tests already covered Step 2):

```bash
uv run python -c "from research_tools import LLMService; import inspect; print('env' in inspect.signature(LLMService.structured_completion).parameters)"
```

**Expected output:**

```text
True
```

## Pass / fail for this step

| Must pass | Must fail |
| --- | --- |
| `SETUP.md` and `README.md` describe per-call `env` with the three known keys | Any new production behavior beyond docs |
| `uv run pytest -q` exit 0 | — |
| Docs do not claim constructor/DI env injection | — |

## Commit checkpoint

```bash
git add SETUP.md README.md
git commit -m "$(cat <<'EOF'
Document per-call API-key env overrides for structured completions.

EOF
)"
```

(Only commit if the user asks.)
