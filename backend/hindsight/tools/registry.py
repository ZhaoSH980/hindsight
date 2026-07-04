"""Tool registry: named tools with JSON-schema params, OpenAI-spec export."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the arguments object
    fn: Callable[..., str]  # returns a JSON string shown to the LLM


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def openai_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, args: dict[str, Any]) -> str:
        return self._tools[name].fn(**args)


def safe_call(registry: ToolRegistry, name: str, args: dict[str, Any]) -> str:
    """LLM-facing dispatch: any failure becomes error JSON the model can read.

    The ReAct loop must never die on a malformed tool call (OverflowError,
    RecursionError, TypeError from unexpected kwargs, unknown tool, ...).
    """
    try:
        return registry.call(name, args)
    except Exception as exc:  # noqa: BLE001 - deliberate catch-all at the LLM boundary
        return json.dumps({"error": f"{type(exc).__name__}: {exc}"})
