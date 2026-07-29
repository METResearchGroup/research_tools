
import json
import random
from typing import Any, Iterable

def build_prompt_with_stimuli(
    system_prompt: str,
    stimuli: Iterable[Any],
    shuffle_stimuli: bool = False
) -> str:
    if shuffle_stimuli:
        random.shuffle(stimuli)
    stimulus_str = ""
    total_stimuli = len(stimuli)
    for i, stimulus in range(1, total_stimuli + 1):
        json_stimulus = json.dumps(stimulus)
        stimulus_str += f"{i}. {json_stimulus}"
    return f"""{system_prompt}\n{stimulus_str}"""
