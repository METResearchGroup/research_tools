# research_tools

Internal Python package with tooling and functionalities designed to improve research productivity.

## Installation

Clone this repository from GitHub, then install it as a locally editable package with `uv`. Full steps—including using it from another project—are in **[SETUP.md](./SETUP.md)**.

```bash
git clone https://github.com/your-org/research_tools.git
cd research_tools
uv sync --extra test
```

## Quick start

```python
from pydantic import BaseModel
from research_tools import LLMService

class LabelResponse(BaseModel):
    label: int

service = LLMService()
result = service.structured_completion(
    messages=[{"role": "user", "content": "Classify this text."}],
    response_model=LabelResponse,
    model="gpt-5.4-nano",
)
print(result.label)
```

Set provider API keys in your environment (for example `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`). Optionally pass the same keys per call via `env={...}` on structured completion APIs; see [SETUP.md](./SETUP.md) for details. Bedrock models use AWS credentials instead of an API key.

## Documentation

See [SETUP.md](./SETUP.md) for:

- Cloning or downloading the repository
- Installing as an editable local package (in this repo or from another project)
- Optional install from GitHub without a local clone
- Environment variables, usage examples, and model config overrides
