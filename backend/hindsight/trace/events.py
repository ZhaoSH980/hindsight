"""Structured trace events. Protocol shared by live stream and replay (spec §5)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "plan_step",
    "tool_call",
    "tool_result",
    "agent_output",
    "validation",
    "context_trim",
    "score",
    "audit",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class TraceEvent(BaseModel):
    type: EventType
    agent: str
    payload: dict[str, Any] = Field(default_factory=dict)
    tokens: int = 0
    ts: str = Field(default_factory=_now_iso)
