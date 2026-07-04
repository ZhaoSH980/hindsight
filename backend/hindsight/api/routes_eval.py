"""Suite launch/status, leaderboard, experience browsing.

Leaderboard reads only what exists: failed runs carry no "outcome" key
(D3 carryover) — every read goes through .get()."""
from __future__ import annotations

import json
import threading
import uuid

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

router = APIRouter()


class StartSuiteRequest(BaseModel):
    case_ids: list[str]
    presets: list[str] = ["base", "memory"]


def _default_suite_executor(state):
    def execute(case_ids: list[str], presets: list[str], suite_id: str) -> None:
        from hindsight.eval.suite import PRESETS, run_suite
        from hindsight.llm.client import LLMConfig, openai_transport
        from hindsight.llm.recording import RecordingLLMClient
        from hindsight.llm.retry import with_retry

        cfg = LLMConfig.from_env()
        llm = RecordingLLMClient(
            transport=with_retry(openai_transport(cfg)),
            db_path=state.root / "llm_calls.sqlite",
            model=cfg.model,
        )
        configs = {name: PRESETS[name].model_copy(update={"model": cfg.model}) for name in presets}

        def work():
            run_suite(
                [state.datasets / cid for cid in case_ids],
                configs,
                llm=llm,
                store=state.store,
                runs_root=state.runs_root,
                suite_id=suite_id,
            )

        threading.Thread(target=work, daemon=True).start()

    return execute


@router.post("/api/eval/suites")
def start_suite(body: StartSuiteRequest, request: Request):
    state = request.app.state.hindsight
    for cid in body.case_ids:
        if not (state.datasets / cid / "meta.json").exists():
            raise HTTPException(status_code=404, detail=f"unknown case {cid}")
    suite_id = f"suite_{uuid.uuid4().hex[:8]}"
    executor = state.suite_executor or _default_suite_executor(state)
    executor(body.case_ids, body.presets, suite_id)
    return {"suite_id": suite_id}


@router.get("/api/eval/suites/{suite_id}")
def suite_status(suite_id: str, request: Request):
    state = request.app.state.hindsight
    runs = state.store.get_runs(suite_id=suite_id)
    summary_path = state.runs_root / "suites" / f"{suite_id}.json"
    summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.exists()
        else None
    )
    return {"suite_id": suite_id, "runs": runs, "summary": summary}


@router.get("/api/leaderboard")
def leaderboard(suite_id: str, request: Request):
    state = request.app.state.hindsight
    summary_path = state.runs_root / "suites" / f"{suite_id}.json"
    if not summary_path.exists():
        raise HTTPException(status_code=404, detail=f"unknown suite {suite_id}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    cases: dict = {}
    for case_name, per_config in summary.get("results", {}).items():
        cases[case_name] = {}
        for config_name, scores in per_config.items():
            outcome = (scores or {}).get("outcome") or {}
            process = (scores or {}).get("process") or {}
            cases[case_name][config_name] = {
                "hit_rate": outcome.get("hit_rate"),
                "brier": outcome.get("brier"),
                "grounding_rate": process.get("grounding_rate"),
                "status": (scores or {}).get("status", "ok"),
            }
    return {"suite_id": suite_id, "configs": summary.get("configs", []), "cases": cases}


@router.get("/api/experiences")
def experiences(request: Request):
    state = request.app.state.hindsight
    rows = state.store.query_experiences("9999-12-31", exclude_case_id="__none__")
    return [json.loads(r["card_json"]) for r in rows]
