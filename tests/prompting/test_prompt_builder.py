"""Unit tests for build_prompt_with_stimuli."""

import json
import random

import pytest

from research_tools.prompting.prompt_builder import build_prompt_with_stimuli


# Pseudocode (Phase 3):
# given system_prompt="You are a rater." and stimuli=[{"id": 1}, {"id": 2}]
# when build_prompt_with_stimuli(system_prompt, stimuli)
# then result starts with system_prompt, then numbered JSON lines in order
#
# given empty stimuli
# when build_prompt_with_stimuli(system_prompt, [])
# then result is system_prompt followed by a trailing newline
#
# given shuffle_stimuli=True and a fixed RNG seed
# when build_prompt_with_stimuli(..., shuffle_stimuli=True)
# then stimuli appear in shuffled order and the caller's list is unchanged
#
# given a non-list iterable (tuple)
# when build_prompt_with_stimuli(..., stimuli=(...))
# then stimuli are still numbered and JSON-serialized


def test_builds_numbered_json_stimuli_after_system_prompt() -> None:
    system_prompt = "You are a rater."
    stimuli = [{"id": 1, "text": "a"}, {"id": 2, "text": "b"}]

    result = build_prompt_with_stimuli(system_prompt, stimuli)

    expected = (
        "You are a rater.\n"
        f"1. {json.dumps(stimuli[0])}\n"
        f"2. {json.dumps(stimuli[1])}"
    )
    assert result == expected


def test_empty_stimuli_returns_system_prompt_with_trailing_newline() -> None:
    result = build_prompt_with_stimuli("System only.", [])
    assert result == "System only.\n"


def test_serializes_non_dict_stimuli() -> None:
    result = build_prompt_with_stimuli("Sys", ["hello", 3])
    expected = f"Sys\n1. {json.dumps('hello')}\n2. {json.dumps(3)}"
    assert result == expected


def test_preserves_order_when_shuffle_disabled() -> None:
    stimuli = [{"n": 1}, {"n": 2}, {"n": 3}]
    result = build_prompt_with_stimuli("S", stimuli, shuffle_stimuli=False)
    assert result.index('"n": 1') < result.index('"n": 2') < result.index('"n": 3')


def test_shuffle_reorders_without_mutating_caller_list(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stimuli = [{"n": 1}, {"n": 2}, {"n": 3}]
    original = [dict(s) for s in stimuli]

    def fake_shuffle(seq: list) -> None:
        seq[:] = [seq[2], seq[0], seq[1]]

    monkeypatch.setattr(random, "shuffle", fake_shuffle)

    result = build_prompt_with_stimuli("S", stimuli, shuffle_stimuli=True)

    assert stimuli == original
    expected = (
        "S\n"
        f"1. {json.dumps({'n': 3})}\n"
        f"2. {json.dumps({'n': 1})}\n"
        f"3. {json.dumps({'n': 2})}"
    )
    assert result == expected


def test_accepts_tuple_stimuli() -> None:
    result = build_prompt_with_stimuli("S", ({"a": 1}, {"b": 2}))
    expected = (
        "S\n"
        f"1. {json.dumps({'a': 1})}\n"
        f"2. {json.dumps({'b': 2})}"
    )
    assert result == expected
