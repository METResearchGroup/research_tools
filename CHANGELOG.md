# CHANGELOG

## 2026-07-29

1. Local commits and PRs now share pre-commit gates (Ruff, Pyright, Lizard, codespell, file hygiene) plus CI pytest and `uv audit`, with LiteLLM bumped to clear known advisories. [PR #3](https://github.com/METResearchGroup/research_tools/pull/3)
2. Fixed `build_prompt_with_stimuli` so it builds numbered JSON stimulus prompts without crashing, optionally shuffles a copy of the input, and is covered by unit tests. [PR #2](https://github.com/METResearchGroup/research_tools/pull/2)
3. Structured completions accept optional per-call `env` API-key overrides (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`) that take precedence over process env for that request only, without mutating shared provider registry state. [PR #1](https://github.com/METResearchGroup/research_tools/pull/1)
