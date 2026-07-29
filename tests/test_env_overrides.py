"""Per-call API-key override resolution helpers."""

import pytest

from research_tools.env import (
    EnvVarsContainer,
    resolve_api_key_for_provider,
    validate_env_overrides,
)


def test_resolve_prefers_override_over_process_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        EnvVarsContainer,
        "get_env_var",
        classmethod(lambda cls, name, required=False: "from-env"),
    )
    overrides = {"OPENAI_API_KEY": "from-dict"}
    assert resolve_api_key_for_provider("openai", overrides) == "from-dict"


def test_resolve_falls_back_to_process_env_when_overrides_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        EnvVarsContainer,
        "get_env_var",
        classmethod(lambda cls, name, required=False: "from-env"),
    )
    assert resolve_api_key_for_provider("openai", None) == "from-env"


def test_validate_env_overrides_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="BOGUS"):
        validate_env_overrides({"OPENAI_API_KEY": "x", "BOGUS": "y"})


def test_resolve_rejects_empty_override_when_required() -> None:
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        resolve_api_key_for_provider(
            "anthropic",
            {"ANTHROPIC_API_KEY": "   "},
            required=True,
        )


def test_resolve_bedrock_returns_none_ignoring_overrides() -> None:
    assert (
        resolve_api_key_for_provider(
            "bedrock",
            {"OPENAI_API_KEY": "ignored"},
        )
        is None
    )


def test_resolve_unknown_provider_raises() -> None:
    with pytest.raises(ValueError):
        resolve_api_key_for_provider("not-a-provider", None)


def test_validate_env_overrides_none_returns_empty_dict() -> None:
    assert validate_env_overrides(None) == {}


def test_validate_env_overrides_returns_copy() -> None:
    original = {"OPENAI_API_KEY": "k"}
    validated = validate_env_overrides(original)
    assert validated == original
    assert validated is not original
