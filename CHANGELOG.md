# CHANGELOG

## 2026-07-29

1. Structured completions accept optional per-call `env` API-key overrides (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`) that take precedence over process env for that request only, without mutating shared provider registry state. [PR #1](https://github.com/METResearchGroup/research_tools/pull/1)
