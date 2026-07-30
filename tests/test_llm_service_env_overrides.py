"""Per-call env overrides on LLMService structured completions."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import BaseModel

from research_tools.env import EnvVarsContainer
from research_tools.llm_service import LLMService
from research_tools.providers.openai_provider import OpenAIProvider
from research_tools.providers.openrouter_provider import OpenRouterProvider
from research_tools.providers.registry import LLMProviderRegistry


class LabelResponse(BaseModel):
    label: int


def _mock_structured_response(label: int = 1) -> Any:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=LabelResponse(label=label).model_dump_json()
                )
            )
        ]
    )


def _reset_openai_provider() -> OpenAIProvider:
    provider = LLMProviderRegistry.get_provider("gpt-5.4-nano")
    assert isinstance(provider, OpenAIProvider)
    provider._initialized = False
    provider._api_key = None
    return provider


def _reset_openrouter_provider() -> OpenRouterProvider:
    provider = LLMProviderRegistry.get_provider("minimax/minimax-m2.5")
    assert isinstance(provider, OpenRouterProvider)
    provider._initialized = False
    provider._api_key = None
    return provider


def _stub_env_keys(monkeypatch: pytest.MonkeyPatch, mapping: dict[str, str]) -> None:
    def fake_get_env_var(cls: type, name: str, required: bool = False) -> str:
        value = mapping.get(name)
        if required and (value is None or not value.strip()):
            raise ValueError(
                f"{name} is required but is missing. "
                f"Please set the {name} environment variable."
            )
        return value or ""

    monkeypatch.setattr(EnvVarsContainer, "get_env_var", classmethod(fake_get_env_var))


def test_structured_completion_uses_dict_api_key_over_process_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_openai_provider()
    _stub_env_keys(monkeypatch, {"OPENAI_API_KEY": "env-key"})
    captured: dict[str, Any] = {}

    def fake_completion(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return _mock_structured_response()

    monkeypatch.setattr(
        "research_tools.llm_service.litellm.completion", fake_completion
    )

    service = LLMService()
    result = service.structured_completion(
        messages=[{"role": "user", "content": "x"}],
        response_model=LabelResponse,
        model="gpt-5.4-nano",
        env={"OPENAI_API_KEY": "dict-key"},
    )
    assert result.label == 1
    assert captured["api_key"] == "dict-key"


def test_structured_completion_uses_process_env_when_env_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_openai_provider()
    _stub_env_keys(monkeypatch, {"OPENAI_API_KEY": "env-key"})
    captured: dict[str, Any] = {}

    def fake_completion(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return _mock_structured_response()

    monkeypatch.setattr(
        "research_tools.llm_service.litellm.completion", fake_completion
    )

    service = LLMService()
    result = service.structured_completion(
        messages=[{"role": "user", "content": "x"}],
        response_model=LabelResponse,
        model="gpt-5.4-nano",
        env=None,
    )
    assert result.label == 1
    assert captured["api_key"] == "env-key"


def test_sequential_calls_do_not_poison_shared_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_openai_provider()
    _stub_env_keys(monkeypatch, {"OPENAI_API_KEY": "env-key"})
    api_keys: list[str] = []

    def fake_completion(**kwargs: Any) -> Any:
        api_keys.append(kwargs["api_key"])
        return _mock_structured_response()

    monkeypatch.setattr(
        "research_tools.llm_service.litellm.completion", fake_completion
    )

    service = LLMService()
    service.structured_completion(
        messages=[{"role": "user", "content": "first"}],
        response_model=LabelResponse,
        model="gpt-5.4-nano",
        env={"OPENAI_API_KEY": "first"},
    )
    service.structured_completion(
        messages=[{"role": "user", "content": "second"}],
        response_model=LabelResponse,
        model="gpt-5.4-nano",
        env=None,
    )
    assert api_keys == ["first", "env-key"]


def test_structured_completion_rejects_unknown_env_key_before_litellm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_openai_provider()
    _stub_env_keys(monkeypatch, {"OPENAI_API_KEY": "env-key"})
    called = False

    def fake_completion(**kwargs: Any) -> Any:
        nonlocal called
        called = True
        return _mock_structured_response()

    monkeypatch.setattr(
        "research_tools.llm_service.litellm.completion", fake_completion
    )

    service = LLMService()
    with pytest.raises(ValueError, match="BOGUS"):
        service.structured_completion(
            messages=[{"role": "user", "content": "x"}],
            response_model=LabelResponse,
            model="gpt-5.4-nano",
            env={"BOGUS": "x"},
        )
    assert called is False


def test_wrong_provider_key_in_env_falls_back_to_process_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_openai_provider()
    _stub_env_keys(monkeypatch, {"OPENAI_API_KEY": "env-key"})
    captured: dict[str, Any] = {}

    def fake_completion(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return _mock_structured_response()

    monkeypatch.setattr(
        "research_tools.llm_service.litellm.completion", fake_completion
    )

    service = LLMService()
    result = service.structured_completion(
        messages=[{"role": "user", "content": "x"}],
        response_model=LabelResponse,
        model="gpt-5.4-nano",
        env={"ANTHROPIC_API_KEY": "a-key"},
    )
    assert result.label == 1
    assert captured["api_key"] == "env-key"


def test_structured_batch_completion_uses_openrouter_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _reset_openrouter_provider()
    _stub_env_keys(monkeypatch, {"OPENROUTER_API_KEY": "env-or-key"})
    captured: dict[str, Any] = {}

    def fake_batch_completion(**kwargs: Any) -> list[Any]:
        captured.update(kwargs)
        return [_mock_structured_response(7)]

    monkeypatch.setattr(
        "research_tools.llm_service.batch_completion",
        fake_batch_completion,
    )

    service = LLMService()
    results = service.structured_batch_completion(
        prompts=["hello"],
        response_model=LabelResponse,
        model="minimax/minimax-m2.5",
        env={"OPENROUTER_API_KEY": "or-key"},
    )
    assert len(results) == 1
    assert results[0].label == 7
    assert captured["api_key"] == "or-key"
