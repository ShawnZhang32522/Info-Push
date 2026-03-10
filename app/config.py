from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    qcc_app_key: str
    qcc_secret_key: str
    qcc_use_mock: bool
    qcc_timeout_seconds: int
    default_page_size: int
    default_days: int
    llm_enabled: bool
    llm_api_url: str
    llm_api_key: str
    llm_model: str


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    return Settings(
        qcc_app_key=os.getenv("QCC_APP_KEY", ""),
        qcc_secret_key=os.getenv("QCC_SECRET_KEY", ""),
        qcc_use_mock=_as_bool(os.getenv("QCC_USE_MOCK", "true"), default=True),
        qcc_timeout_seconds=int(os.getenv("QCC_TIMEOUT_SECONDS", "20")),
        default_page_size=int(os.getenv("DEFAULT_PAGE_SIZE", "10")),
        default_days=int(os.getenv("DEFAULT_DAYS", "7")),
        llm_enabled=_as_bool(os.getenv("LLM_ENABLED", "false"), default=False),
        llm_api_url=os.getenv("LLM_API_URL", ""),
        llm_api_key=os.getenv("LLM_API_KEY", ""),
        llm_model=os.getenv("LLM_MODEL", ""),
    )


SETTINGS = load_settings()

