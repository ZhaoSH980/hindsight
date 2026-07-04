"""Application state shared by all routers."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from hindsight.store.db import Store

_REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass
class AppState:
    root: Path
    store: Store
    run_executor: Callable[..., Any] | None = None    # tests inject; None = real
    suite_executor: Callable[..., Any] | None = None

    @property
    def datasets(self) -> Path:
        return self.root / "datasets"

    @property
    def runs_root(self) -> Path:
        return self.root / "runs"


def make_state(repo_root: Path | None = None) -> AppState:
    root = Path(repo_root) if repo_root else _REPO_ROOT
    return AppState(root=root, store=Store(root / "hindsight.db"))
