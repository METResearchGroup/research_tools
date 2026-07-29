# Setup guide

This guide is for new users who want to install and use `research_tools` locally.

## What is this package?

`research_tools` is a small library that wraps [LiteLLM](https://github.com/BerriAI/litellm) for structured completions:

- `LLMService` for single and batch structured completions validated with Pydantic
- Provider routing for OpenAI, Anthropic, OpenRouter, and Amazon Bedrock
- YAML-backed model configuration (`src/research_tools/config/models.yaml`)
- Retry logic with provider-aware rate-limit handling
- Internal exception types for consistent error handling

Import path:

```python
from research_tools import LLMService, get_llm_service
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

Install `uv` if you do not already have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 1. Download the repository

Clone from GitHub (replace the URL with your org's repository):

```bash
git clone https://github.com/your-org/research_tools.git
cd research_tools
```

Or download a ZIP from the GitHub UI and extract it, then `cd` into the extracted folder.

After download, the tree should look like:

```text
research_tools/
├── pyproject.toml
├── README.md
├── SETUP.md
├── src/
│   └── research_tools/
│       ├── __init__.py
│       ├── llm_service.py
│       ├── exceptions.py
│       ├── retry.py
│       ├── env.py
│       ├── aws/
│       ├── config/
│       └── providers/
└── tests/
```

## 2. Install as a locally editable package

### Develop inside this repository

From the repository root:

```bash
uv sync --extra test
```

That creates a virtual environment and installs `research_tools` in editable mode along with test dependencies.

Run the tests:

```bash
uv run pytest
```

Build a wheel locally (optional):

```bash
uv build
```

Built artifacts appear in `dist/`.

### Use from another project (editable path install)

If you want a separate project to import `research_tools` while still editing this checkout live, add it as an editable path dependency.

In the consuming project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "research_tools",
]

[tool.uv.sources]
research_tools = { path = "../research_tools", editable = true }
```

Adjust the `path` so it points at this repository root (the folder that contains `pyproject.toml`). Then:

```bash
uv sync
```

Alternatively, from the consuming project:

```bash
uv add --editable /absolute/or/relative/path/to/research_tools
```

### Install from GitHub without a local clone

If you only need to consume the package and do not need local edits, pin it from Git in the consuming project's `pyproject.toml`:

```toml
[project]
dependencies = [
    "research_tools",
]

[tool.uv.sources]
research_tools = { git = "https://github.com/your-org/research_tools.git", branch = "main" }
```

Or pin a release tag:

```toml
[tool.uv.sources]
research_tools = { git = "https://github.com/your-org/research_tools.git", tag = "v0.1.0" }
```

Then:

```bash
uv sync
```

## 3. Environment variables

Providers read credentials from the environment (or a `.env` file loaded by `python-dotenv`):

| Variable | Used by |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI models |
| `ANTHROPIC_API_KEY` | Anthropic models |
| `OPENROUTER_API_KEY` | OpenRouter models |
| `AWS_PROFILE` / default AWS credential chain | Bedrock models |

The same three API-key names (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`) may also be passed per call via `env={...}` on `structured_completion` / `structured_batch_completion`. Dict values override process env for that call only; unknown keys are rejected. Bedrock still uses the AWS credential chain (not these API-key vars).

## 4. Basic usage

```python
from pydantic import BaseModel
from research_tools import LLMService

class LabelResponse(BaseModel):
    label: int

service = LLMService()
result = service.structured_completion(
    messages=[{"role": "user", "content": "Return a label for this text."}],
    response_model=LabelResponse,
    model="gpt-5.4-nano",
)
print(result.label)
```

Per-call API key override (process env remains the fallback when a key is omitted):

```python
result = service.structured_completion(
    messages=[{"role": "user", "content": "Return a label for this text."}],
    response_model=LabelResponse,
    model="gpt-5.4-nano",
    env={"OPENAI_API_KEY": "..."},
)
```

Batch API:

```python
results = service.structured_batch_completion(
    prompts=["first prompt", "second prompt"],
    response_model=LabelResponse,
    model="gpt-5.4-nano",
)
```

## 5. Customizing model configuration

Default model settings live in `src/research_tools/config/models.yaml`. To override the config path at runtime (for tests or deployment-specific configs):

```python
from pathlib import Path
from research_tools.config.model_registry import ModelConfigRegistry

ModelConfigRegistry.set_config_path(Path("/path/to/custom-models.yaml"))
```

## 6. Releasing a new version

1. Bump `version` in `pyproject.toml`.
2. Run `uv run pytest`.
3. Run `uv build`.
4. Commit, tag (`v0.1.1`), and push the tag.
5. Update consuming projects to the new tag, or republish the wheel.
