"""Flight recorder: append-only jsonl + in-memory list."""
from __future__ import annotations

from pathlib import Path

from hindsight.trace.events import TraceEvent


class TraceRecorder:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.run_dir / "trace.jsonl"
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
