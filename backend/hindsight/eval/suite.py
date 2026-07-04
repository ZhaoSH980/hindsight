"""EvalSuite: N cases x M configs with a single experience snapshot.

Cases run in as_of ascending order (spec §3.5: later cases may legally use
earlier cases' experience — but only cards that existed BEFORE the suite
started, so config comparisons stay order-independent)."""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Callable

from hindsight.agents.orchestrator import run_research
from hindsight.data.cases import load_case
from hindsight.schemas import RunConfig
from hindsight.store.db import Store, now_iso

PRESETS: dict[str, RunConfig] = {
    "base": RunConfig(),
    "memory": RunConfig(memory_on=True),
    "tight": RunConfig(memory_on=True, context_budget=2000),
}


def run_suite(
    case_dirs: list[Path],
    configs: dict[str, RunConfig],
    *,
    llm: Any,
    store: Store,
    runs_root: Path,
    run_fn: Callable[..., Any] = run_research,
) -> str:
    suite_id = f"suite_{uuid.uuid4().hex[:8]}"
    suite_started_at = now_iso()  # single snapshot BEFORE any run
    ordered = sorted(case_dirs, key=lambda d: load_case(Path(d)).meta.as_of)
    results: dict[str, dict[str, Any]] = {}
    for case_dir in ordered:
        case_name = Path(case_dir).name
        results[case_name] = {}
        for config_name, config in configs.items():
            result = run_fn(
                case_dir,
                config,
                llm=llm,
                store=store,
                runs_root=runs_root,
                suite_id=suite_id,
                suite_started_at=suite_started_at,
            )
            results[case_name][config_name] = result.scores
    summary = {
        "suite_id": suite_id,
        "started_at": suite_started_at,
        "cases": [Path(d).name for d in ordered],
        "configs": list(configs),
        "results": results,
    }
    out = Path(runs_root) / "suites" / f"{suite_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return suite_id
