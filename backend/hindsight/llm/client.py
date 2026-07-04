"""LLM config from .env and the production transport (openai SDK)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from pydantic import BaseModel

Transport = Callable[[dict[str, Any]], dict[str, Any]]


class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls, dotenv_path: Path | None = None) -> "LLMConfig":
        load_dotenv(dotenv_path)  # repo-root .env by default
        return cls(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ["LLM_API_KEY"],
            model=os.environ["LLM_MODEL"],
        )


def openai_transport(config: LLMConfig) -> Transport:
    from openai import OpenAI

    client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def send(request: dict[str, Any]) -> dict[str, Any]:
        response = client.chat.completions.create(**request)
        return response.model_dump()

    return send
