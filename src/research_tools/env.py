"""Environment variable loading for LLM provider credentials."""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

ENV_VAR_TYPES: Final[dict[str, type[str]]] = {
    "OPENAI_API_KEY": str,
    "ANTHROPIC_API_KEY": str,
    "OPENROUTER_API_KEY": str,
}

PROVIDER_API_KEY_ENV_VARS: Final[dict[str, str]] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def validate_env_overrides(env: dict[str, str] | None) -> dict[str, str]:
    """Return a copy of env, or {}. Raise ValueError if any key is not in ENV_VAR_TYPES."""
    if env is None:
        return {}
    illegal = [key for key in env if key not in ENV_VAR_TYPES]
    if illegal:
        raise ValueError(
            f"Unknown env override key(s): {', '.join(sorted(illegal))}. "
            f"Allowed keys: {', '.join(sorted(ENV_VAR_TYPES))}."
        )
    return dict(env)


def resolve_api_key_for_provider(
    provider_name: str,
    env_overrides: dict[str, str] | None = None,
    *,
    required: bool = True,
) -> str | None:
    """
    Resolve API key for provider_name.

    - bedrock: always return None (ignore overrides for API-key purposes).
    - unknown provider_name: raise ValueError.
    - if overrides contain the mapped key: use that value
      (empty/whitespace → ValueError when required).
    - else: EnvVarsContainer.get_env_var(mapped_key, required=required);
      return None when not required and missing.
    """
    if provider_name == "bedrock":
        return None

    mapped_key = PROVIDER_API_KEY_ENV_VARS.get(provider_name)
    if mapped_key is None:
        raise ValueError(f"Unknown provider_name: {provider_name!r}")

    overrides = validate_env_overrides(env_overrides)
    if mapped_key in overrides:
        value = overrides[mapped_key]
        if not value.strip():
            if required:
                raise ValueError(
                    f"{mapped_key} is required but is empty. "
                    f"Please set the {mapped_key} environment variable to a non-empty value."
                )
            return None
        return value

    raw = EnvVarsContainer.get_env_var(mapped_key, required=required)
    if not required and (raw is None or not str(raw).strip()):
        return None
    return str(raw)


class EnvVarsContainer:
    """Thread-safe singleton container for environment variables."""

    _instance: EnvVarsContainer | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        self._initialized = False
        self._env_vars: dict[str, str | None] = {}
        self._env_var_types: dict[str, type[str]] = ENV_VAR_TYPES
        self._init_lock = threading.Lock()

    @classmethod
    def get_env_var(cls, name: str, required: bool = False) -> str:
        """Get an environment variable after container initialization."""
        instance: EnvVarsContainer = cls._get_instance()
        raw: str | None = instance._env_vars.get(name)

        if required:
            if raw is None:
                raise ValueError(
                    f"{name} is required but is missing. "
                    f"Please set the {name} environment variable."
                )
            if isinstance(raw, str) and not raw.strip():
                raise ValueError(
                    f"{name} is required but is empty. "
                    f"Please set the {name} environment variable to a non-empty value."
                )

        if raw is None:
            return ""
        return str(raw)

    @classmethod
    def _get_instance(cls) -> EnvVarsContainer:
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        cls._instance._ensure_initialized()
        return cls._instance

    def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        with self._init_lock:
            if self._initialized:
                return
            self._initialize_env_vars()
            self._initialized = True

    def _initialize_env_vars(self) -> None:
        load_dotenv()
        for key in self._env_var_types:
            self._env_vars[key] = os.getenv(key)
