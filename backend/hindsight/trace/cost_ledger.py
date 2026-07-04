"""Per-agent token accounting (spec §3.4 track C)."""
from __future__ import annotations

from collections import defaultdict


class CostLedger:
    def __init__(self) -> None:
        self._by_agent: dict[str, dict[str, int]] = defaultdict(
            lambda: {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
        )

    def add(self, agent: str, prompt_tokens: int, completion_tokens: int) -> None:
        row = self._by_agent[agent]
        row["prompt_tokens"] += prompt_tokens
        row["completion_tokens"] += completion_tokens
        row["calls"] += 1

    def summary(self) -> dict[str, dict[str, int]]:
        return {agent: dict(row) for agent, row in self._by_agent.items()}

    def total_tokens(self) -> int:
        return sum(
            row["prompt_tokens"] + row["completion_tokens"]
            for row in self._by_agent.values()
        )
