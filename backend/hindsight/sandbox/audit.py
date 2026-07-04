"""Audit log: every sandboxed data access leaves a row (spec §3.2)."""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)
    data_max_date: date | None = None
    note: str = ""


class AuditLog:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(
        self,
        tool: str,
        params: dict[str, Any],
        data_max_date: date | None = None,
        note: str = "",
    ) -> None:
        self.entries.append(
            AuditEntry(tool=tool, params=params, data_max_date=data_max_date, note=note)
        )

    def as_dicts(self) -> list[dict[str, Any]]:
        return [e.model_dump(mode="json") for e in self.entries]
