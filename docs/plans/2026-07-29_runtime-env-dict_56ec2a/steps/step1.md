# Step 1: Define runtime env contract and resolution helpers

## Remember
- Exact file paths always
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Delegated tasks must be impossible to misread.

## Goal

Freeze the public contract for per-call credential overrides and implement a small resolver that maps `(provider_name, env_overrides) → api_key | None`, with process-env fallback. Lock behavior with failing tests before Step 2 wires the service.

## Scope

- **Caller (this step):** test modules exercising the new resolver; production callers arrive in Step 2.
- **Slice:** validate overrides → map provider to env-var name → resolve key (override or `EnvVarsContainer`) → return value or raise.
- **Out of scope:** changing `LLMService`, providers’ `initialize`, docs, Bedrock AWS vars.

## Files

### Inspect

- `/Users/mark/src/work/research_tools/src/research_tools/env.py`
- `/Users/mark/src/work/research_tools/tests/test_env_loading.py`
- `/Users/mark/src/work/research_tools/src/research_tools/providers/openai_provider.py` (env key name: `OPENAI_API_KEY`)
- `/Users/mark/src/work/research_tools/src/research_tools/providers/anthropic_provider.py` (`ANTHROPIC_API_KEY`)
- `/Users/mark/src/work/research_tools/src/research_tools/providers/openrouter_provider.py` (`OPENROUTER_API_KEY`)
- `/Users/mark/src/work/research_tools/src/research_tools/providers/bedrock_provider.py` (no API key)

### Allowed to change

- `/Users/mark/src/work/research_tools/src/research_tools/env.py`
- `/Users/mark/src/work/research_tools/tests/test_env_loading.py`
- Create `/Users/mark/src/work/research_tools/tests/test_env_overrides.py` if preferred over expanding `test_env_loading.py`

### Forbidden to change

- `/Users/mark/src/work/research_tools/src/research_tools/llm_service.py`
- `/Users/mark/src/work/research_tools/src/research_tools/providers/**`
- `/Users/mark/src/work/research_tools/SETUP.md`
- `/Users/mark/src/work/research_tools/README.md`
- `/Users/mark/src/work/research_tools/src/research_tools/__init__.py`

## Contract freeze

Add to `/Users/mark/src/work/research_tools/src/research_tools/env.py` (names may be adjusted only if tests use the same public names):

1. **Allowed keys** — reuse `ENV_VAR_TYPES` keys only:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `OPENROUTER_API_KEY`

2. **Provider → key map** (exact):
   - `openai` → `OPENAI_API_KEY`
   - `anthropic` → `ANTHROPIC_API_KEY`
   - `openrouter` → `OPENROUTER_API_KEY`
   - `bedrock` → no API-key env var (resolver returns `None` without reading process env for API keys)

3. **Public helpers** (signatures):

```python
def validate_env_overrides(env: dict[str, str] | None) -> dict[str, str]:
    """Return a copy of env, or {}. Raise ValueError if any key is not in ENV_VAR_TYPES."""

def resolve_api_key_for_provider(
    provider_name: str,
    env_overrides: dict[str, str] | None = None,
    *,
    required: bool = True,
) -> str | None:
    """
    Resolve API key for provider_name.
    - bedrock: always return None (ignore overrides for API-key purposes).
    - unknown provider_name: raise ValueError.
    - if overrides contain the mapped key: use that value (empty/whitespace → ValueError when required).
    - else: EnvVarsContainer.get_env_var(mapped_key, required=required); return None when not required and missing.
    """
```

4. **Precedence:** non-empty override for the mapped key wins over `EnvVarsContainer` / process env for that call’s resolution. Do not mutate `os.environ` or the `EnvVarsContainer` singleton.

5. **Unknown keys:** `validate_env_overrides({"NOT_A_KEY": "x"})` raises `ValueError` mentioning the illegal key.

## Test design (write failing tests first)

### Pseudocode

```text
given overrides={"OPENAI_API_KEY": "from-dict"} and process env has OPENAI_API_KEY=from-env
when resolve_api_key_for_provider("openai", overrides)
then return "from-dict"

given overrides=None and EnvVarsContainer returns "from-env" for OPENAI_API_KEY
when resolve_api_key_for_provider("openai", None)
then return "from-env"

given overrides={"OPENAI_API_KEY": "x", "BOGUS": "y"}
when validate_env_overrides(overrides)
then raise ValueError matching BOGUS

given overrides={"ANTHROPIC_API_KEY": "   "} and required=True
when resolve_api_key_for_provider("anthropic", overrides)
then raise ValueError matching ANTHROPIC_API_KEY

given any overrides including OPENAI_API_KEY
when resolve_api_key_for_provider("bedrock", overrides)
then return None

given provider_name="not-a-provider"
when resolve_api_key_for_provider("not-a-provider", None)
then raise ValueError
```

### Commands

```bash
cd /Users/mark/src/work/research_tools
uv run pytest tests/test_env_loading.py tests/test_env_overrides.py -q
```

**Expected after tests exist, before implementation:** failures on new resolver assertions / `ImportError` for missing symbols.

**Expected after this step’s implementation:** those tests pass. Existing `test_anthropic_api_key_registered` still passes.

## Implementation notes

- Keep helpers pure relative to process state except the intentional `EnvVarsContainer.get_env_var` fallback.
- Do not change singleton initialization behavior in this step beyond what the helpers need.
- Prefer one small module section in `env.py` over a new file (YAGNI).

## Pass / fail for this step

| Must pass | Must fail / not yet required |
| --- | --- |
| New resolver/validation tests green | Service-level per-call tests (Step 2) |
| `uv run pytest tests/test_env_loading.py tests/test_env_overrides.py -q` exit 0 | Full suite not required yet, but must not break existing env tests |
| No edits under `llm_service.py` or `providers/` | — |

## Commit checkpoint

After green resolver tests:

```bash
git add src/research_tools/env.py tests/test_env_loading.py tests/test_env_overrides.py
git commit -m "$(cat <<'EOF'
Add per-call API-key override resolution helpers.

EOF
)"
```

(Only commit if the user asks for a commit; otherwise leave staged work uncommitted.)
