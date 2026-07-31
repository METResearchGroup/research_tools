"""Example: run structured LLM completions over items with ``llm.runner``.

Illustrates the call-site pattern:

1. Define a Pydantic ``response_model``.
2. Provide ``prompt_fn(item) -> messages``.
3. Provide ``writer_map_fn(item, result) -> dict`` for persistence.
4. Call ``run(...)``.

Run (requires provider credentials for the chosen model)::

    uv run python -m research_tools.llm.recipes.runner
"""

from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel, Field

from research_tools.llm.runner import run
from research_tools.prompting import build_prompt_with_stimuli

SYSTEM_PROMPT = (
    "You label social-media posts for moderation. "
    "Given one or more posts, decide whether the content should be removed. "
    "Respond with the structured schema only."
)

# Toy dataset — replace with a real loader in experiments.
ITEMS: list[dict[str, Any]] = [
    {
        "message_id": "msg-001",
        "original_text": "Have a great day everyone!",
        "mirror_text": "Everyone should have a great day!",
        "keep_remove_label": 0,
    },
    {
        "message_id": "msg-002",
        "original_text": "Buy fake followers now!!!",
        "mirror_text": "Purchase fake followers immediately!!!",
        "keep_remove_label": 1,
    },
]


class IsRemoveResult(BaseModel):
    """Structured LLM response for a keep/remove decision."""

    is_remove: bool = Field(description="True if the post should be removed.")
    rationale: str = Field(description="Brief reason for the decision.")


def prompt_fn(item: dict[str, Any]) -> list[dict]:
    """Build chat messages for one item."""
    stimuli = [
        {"post": item["original_text"]},
        {"post": item["mirror_text"]},
    ]
    content = build_prompt_with_stimuli(
        system_prompt=SYSTEM_PROMPT,
        stimuli=stimuli,
        shuffle_stimuli=True,
    )
    return [{"role": "user", "content": content}]


def writer_map_fn(item: dict[str, Any], result: IsRemoveResult) -> dict[str, Any]:
    """Map (item, LLM result) to the dict written as a JSON result file."""
    predicted_label = int(result.is_remove)
    return {
        "message_id": item["message_id"],
        "keep_remove_label": item["keep_remove_label"],
        "predicted_label": predicted_label,
        "is_remove": result.is_remove,
        "rationale": result.rationale,
    }


def main() -> None:
    out_dir = run(
        ITEMS,
        prompt_fn=prompt_fn,
        response_model=IsRemoveResult,
        model="gpt-5.4-nano",
        output_base_path=os.getcwd(),
        writer_map_fn=writer_map_fn,
        run_metadata={"example": "recipes.runner", "seed": 42},
        temperature=0.0,
    )
    print(f"Wrote run outputs to {out_dir}")


if __name__ == "__main__":
    main()
