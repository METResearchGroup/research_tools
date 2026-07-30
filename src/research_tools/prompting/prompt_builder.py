import json
import random
from collections.abc import Iterable
from typing import Any


def build_prompt_with_stimuli(
    system_prompt: str,
    stimuli: Iterable[Any],
    shuffle_stimuli: bool = False,
) -> str:
    items = list(stimuli)
    if shuffle_stimuli:
        random.shuffle(items)

    stimulus_lines = [
        f"{i}. {json.dumps(stimulus)}" for i, stimulus in enumerate(items, start=1)
    ]
    stimulus_str = "\n".join(stimulus_lines)
    return f"{system_prompt}\n{stimulus_str}"
