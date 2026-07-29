# Step 2: Wire per-call env through structured completion paths

## Remember
- Exact file paths always
- Exact commands with expected output
- DRY, YAGNI, TDD, frequent commits
- Delegated tasks must be impossible to misread.

## Goal

Expose optional `env` on the public structured-completion APIs and use Step 1’s resolver so each request gets the correct API key without permanently binding shared provider registry instances to that override.

## Scope

- **Caller:** `LLMService.structured_completion` and `LLMService.structured_batch_completion` in `/Users/mark/src/work/research_tools/src/research_tools/llm_service.py`.
- **Slice:** accept `env` → validate → get provider → resolve API key for that provider → pass key on this completion (and retries) → leave shared provider `_api_key` usable as fallback when `env` omits the key.
- **Out of scope:** constructor/`get_llm_service` env injection; AWS/Bedrock credential overrides; changing LiteLLM itself; docs (Step 3).

## Files

### Inspect

- `/Users/mark/src/work/research_tools/src/research_tools/llm_service.py` (especially `_get_provider_for_model`, `_chat_completion`, `_batch_completion`, `structured_completion`, `structured_batch_completion`)
- `/Users/mark/src/work/research_tools/src/research_tools/env.py` (helpers from Step 1)
- `/Users/mark/src/work/research_tools/src/research_tools/providers/base.py`
- `/Users/mark/src/work/research_tools/src/research_tools/providers/registry.py`
- `/Users/mark/src/work/research_tools/tests/test_anthropic_provider.py`

### Allowed to change

- `/Users/mark/src/work/research_tools/src/research_tools/llm_service.py`
- Create `/Users/mark/src/work/research_tools/tests/test_llm_service_env_overrides.py`
- Providers **only if** required to stop “first `initialize` wins” from blocking per-call keys — preferred approach below avoids provider edits; if a provider edit is unavoidable, limit to `initialize` allowing explicit `api_key` update when provided, and document why in the PR/commit message.

### Forbidden to change

- `/Users/mark/src/work/research_tools/SETUP.md`
- `/Users/mark/src/work/research_tools/README.md`
- `/Users/mark/src/work/research_tools/src/research_tools/aws/**`
- Step 1 public resolver signatures (except bugfixes discovered by these tests)

## Contract freeze (public API)

On both methods, add optional keyword-only-friendly parameter (positional after existing kwargs is fine if documented):

```python
def structured_completion(
    self,
    messages: list[dict],
    response_model: type[T],
    model: str | None = None,
    env: dict[str, str] | None = None,
    **kwargs,
) -> T: ...

def structured_batch_completion(
    self,
    prompts: list[str],
    response_model: type[T],
    model: str | None = None,
    role: str = "user",
    env: dict[str, str] | None = None,
    **kwargs,
) -> list[T]: ...
```

**Semantics:**

1. Call `validate_env_overrides(env)` at the start of each public method (before provider work).
2. Obtain provider via existing `_get_provider_for_model(model)` (lazy `initialize()` from process env when no override is needed remains OK).
3. Resolve request API key with `resolve_api_key_for_provider(provider.provider_name, env)`.
4. For providers that use API keys: set `completion_kwargs["api_key"]` to the **resolved** key for this request, not solely `provider.api_key`.
5. For Bedrock (`resolve` returns `None`): do not set `api_key` on the completion (same as today).
6. Thread `env` (or the already-resolved key) through `_complete_and_validate_structured*` → `_chat_completion` / `_batch_completion` so retries use the same per-call key.
7. Do **not** write the override into `os.environ` or `EnvVarsContainer._env_vars`.
8. Do **not** permanently overwrite a shared provider’s stored key with a per-call override in a way that later calls without `env` keep using the override. Preferred pattern: keep provider init on process env; inject override only into `completion_kwargs["api_key"]` for that request.

**Internal signature shape (implementer chooses exact names, must match tests):**

- `_chat_completion` / `_batch_completion` accept either `env` or an explicit `api_key_override: str | None` derived by the public methods.
- Private retry helpers must receive enough state to re-apply the same key.

## Test design (failing first)

Prefer public seams: monkeypatch `litellm.completion` / `batch_completion` (or the service’s `_chat_completion`) to capture kwargs, and monkeypatch `EnvVarsContainer.get_env_var` for process-env values.

### Pseudocode

```text
given process env OPENAI_API_KEY=env-key
and litellm.completion mocked to return a valid structured JSON response
when structured_completion(..., model=<openai model>, env={"OPENAI_API_KEY": "dict-key"})
then mocked completion received api_key="dict-key"

given process env OPENAI_API_KEY=env-key
when structured_completion(..., model=<openai model>, env=None)
then mocked completion received api_key="env-key"

given two sequential calls on the same LLMService / shared registry:
  first env={"OPENAI_API_KEY": "first"}
  second env=None (process has "env-key")
then first completion uses "first" and second uses "env-key"

given env={"BOGUS": "x"}
when structured_completion(..., env=env)
then raise ValueError matching BOGUS before any LiteLLM call

given env={"ANTHROPIC_API_KEY": "a-key"} and model is an OpenAI model
when structured_completion(...)
then OpenAI path still resolves OPENAI_API_KEY from process env (anthropic key ignored for this provider)

given structured_batch_completion with env={"OPENROUTER_API_KEY": "or-key"} and an openrouter model
then batch path passes api_key="or-key"
```

Use a real model id from `/Users/mark/src/work/research_tools/src/research_tools/config/models.yaml` / provider `supported_models` so registry lookup succeeds. Mock network I/O.

### Commands

```bash
cd /Users/mark/src/work/research_tools
uv run pytest tests/test_llm_service_env_overrides.py tests/test_env_overrides.py tests/test_env_loading.py -q
```

**Expected before implementation:** new service tests fail.

**Expected after implementation:** those tests pass; existing provider/env tests still pass.

```bash
uv run pytest -q
```

**Expected:** full suite exit 0 before declaring Step 2 done.

## Implementation order (TDD / dependency order)

1. Add failing tests in `tests/test_llm_service_env_overrides.py`.
2. Add `env` parameter to public methods; call `validate_env_overrides`.
3. Resolve key via `resolve_api_key_for_provider` after provider selection.
4. Plumb resolved key into `_chat_completion` / `_batch_completion` (and retry wrappers) so `completion_kwargs["api_key"]` uses it when not `None`.
5. Confirm sequential call test proves no shared-state poisoning.
6. Run full `uv run pytest -q`.

## Pass / fail for this step

| Must pass | Must fail / not yet required |
| --- | --- |
| All tests in `tests/test_llm_service_env_overrides.py` | Docs updates (Step 3) |
| Step 1 env tests still green | — |
| `uv run pytest -q` exit 0 | — |
| No mutation of process env / EnvVarsContainer from per-call overrides | — |

## Commit checkpoint

```bash
git add src/research_tools/llm_service.py tests/test_llm_service_env_overrides.py
# include any narrowly scoped provider fix if required
git commit -m "$(cat <<'EOF'
Support per-call API-key env overrides on structured completions.

EOF
)"
```

(Only commit if the user asks.)
