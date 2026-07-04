"""The run orchestrator: a deterministic state machine around the agents.

Stage order: contamination probe -> experience retrieval (memory_on) ->
planner (bounded ReAct) -> evidence bundle -> analyst/critic loop ->
outcome grading -> judge -> experience write (always) -> persistence.

Grading reads bars DIRECTLY from the case's frozen snapshot, bypassing the
sandbox on purpose: evaluation is entitled to realized data. Agents never
receive anything derived from that read.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from hindsight.agents.critic import produce_memo
from hindsight.agents.planner import FINISH_TOOL, run_planner
from hindsight.agents.prompts import case_brief, experience_block
from hindsight.agents.researcher import EvidenceManager
from hindsight.data.cases import load_case
from hindsight.eval.contamination import run_contamination_probe
from hindsight.eval.judge import judge_scores, run_judge
from hindsight.eval.outcome_grader import GradedClaim, aggregate, grade_claims
from hindsight.llm.recording import RecordingLLMClient
from hindsight.memory.experience import ExperienceRetriever, build_card, render_cards
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.gate import SandboxedCorpus, SandboxedMarketData
from hindsight.schemas import GradeStatus, Memo, RunConfig
from hindsight.store.db import Store
from hindsight.tools.calc import make_calc_tool
from hindsight.tools.corpus_search import make_corpus_tool
from hindsight.tools.market_data import make_market_tool
from hindsight.tools.registry import ToolRegistry, safe_call
from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder

FAR_FUTURE = date(2100, 1, 1)


@dataclass
class RunResult:
    run_id: str
    memo: Memo | None
    scores: dict
    unverified: bool
    run_dir: Path


def _new_run_id(case_id: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"run_{case_id}_{stamp}_{uuid.uuid4().hex[:6]}"


def _forward_audit(trace: TraceRecorder, audit: AuditLog, start: int) -> int:
    for entry in audit.entries[start:]:
        trace.emit(
            TraceEvent(type="audit", agent="sandbox", payload=entry.model_dump(mode="json"))
        )
    return len(audit.entries)


def _memo_markdown(memo: Memo, graded: list[GradedClaim]) -> str:
    status = {g.claim.claim_id: g for g in graded}
    lines = [
        "# Research memo",
        "",
        "## Background",
        memo.background,
        "",
        "## Bull case",
        memo.bull_case,
        "",
        "## Bear case",
        memo.bear_case,
        "",
        "## Conclusion",
        memo.conclusion,
        "",
        "## Claims",
    ]
    for c in memo.claims:
        g = status.get(c.claim_id)
        verdict = f" -> **{g.status.value}** ({g.detail})" if g else ""
        lines.append(
            f"- `{c.claim_id}` [{c.type.value}, {c.horizon_days}d, conf {c.confidence}] "
            f"{c.statement}{verdict}"
        )
    return "\n".join(lines) + "\n"


def run_research(
    case_dir: Path,
    config: RunConfig,
    *,
    llm: RecordingLLMClient,
    store: Store,
    runs_root: Path,
    suite_id: str | None = None,
    suite_started_at: str | None = None,
) -> RunResult:
    case = load_case(Path(case_dir))
    as_of = case.meta.as_of
    run_id = _new_run_id(case.meta.case_id)
    run_dir = Path(runs_root) / run_id
    trace = TraceRecorder(run_dir=run_dir)
    ledger = CostLedger()
    audit = AuditLog()
    audit_seen = 0

    store.upsert_run(run_id, case.meta.case_id, config.model_dump_json(), "running", suite_id=suite_id)

    corpus = SandboxedCorpus(BM25Retriever(case.chunks), as_of=as_of, audit=audit)
    market = SandboxedMarketData(case.bars_source, as_of=as_of, audit=audit)
    evidence = EvidenceManager(config.context_budget)
    registry = ToolRegistry()
    registry.register(make_corpus_tool(corpus, evidence_sink=evidence))
    registry.register(make_market_tool(market, case.meta.ticker))
    registry.register(make_calc_tool())
    registry.register(FINISH_TOOL)

    probe_text = run_contamination_probe(llm, case.meta.ticker, as_of, ledger)

    cards = []
    if config.memory_on:
        retriever = ExperienceRetriever(store)
        cards = retriever.retrieve(
            f"{case.meta.ticker} {' '.join(case.meta.tags)} {case.meta.title}",
            as_of=as_of,
            exclude_case_id=case.meta.case_id,
            created_before=suite_started_at,
        )
    brief = case_brief(case.meta) + experience_block(render_cards(cards))

    temperature = float(config.temperature)
    run_planner(
        llm=llm, registry=registry, user_brief=brief,
        max_steps=config.max_steps, temperature=temperature,
        trace=trace, ledger=ledger,
    )
    audit_seen = _forward_audit(trace, audit, audit_seen)

    bundle = evidence.bundle(trace)
    market_summary = safe_call(registry, "price_history", {"lookback_days": 60})
    audit_seen = _forward_audit(trace, audit, audit_seen)

    memo, unverified = produce_memo(
        llm, bundle, case.meta, market_summary, temperature, trace, ledger
    )
    if memo is None:
        scores = {"status": "failed_validation", "cost": ledger.summary(),
                  "contamination_probe": probe_text[:2000]}
        (run_dir / "scores.json").write_text(json.dumps(scores, indent=1), encoding="utf-8")
        store.upsert_run(run_id, case.meta.case_id, config.model_dump_json(), "failed",
                         scores_json=json.dumps(scores), suite_id=suite_id)
        return RunResult(run_id, None, scores, True, run_dir)

    # ---- evaluation side: deliberately outside the sandbox ----
    bars = case.bars_source.get_bars(case.meta.ticker, as_of - timedelta(days=800), FAR_FUTURE)
    graded = grade_claims(memo.claims, bars, as_of)
    if unverified:
        for g in graded:
            g.status = GradeStatus.ungradable  # unverified memo claims never score
    agg = aggregate(graded)
    report = run_judge(llm, memo, graded, evidence.evidence_map(), temperature, ledger)
    jscores = judge_scores(report)

    baseline = max((i for i, b in enumerate(bars) if b.date <= as_of), default=None)
    if baseline is None:
        window_end = as_of
    else:
        end_i = min(baseline + case.meta.outcome_window_days, len(bars) - 1)
        window_end = bars[end_i].date
    card = build_card(case.meta, run_id, graded, report, window_end)
    ExperienceRetriever(store).write(card)  # write-always (spec §3.5)

    scores = {
        "outcome": agg,
        "process": jscores,
        "cost": ledger.summary(),
        "contamination_probe": probe_text[:2000],
        "unverified": unverified,
    }
    trace.emit(TraceEvent(type="score", agent="eval", payload={"outcome": agg, "process": jscores}))
    audit_seen = _forward_audit(trace, audit, audit_seen)

    (run_dir / "memo.md").write_text(_memo_markdown(memo, graded), encoding="utf-8", newline="\n")
    (run_dir / "claims.json").write_text(
        json.dumps(
            [
                {
                    **g.claim.model_dump(mode="json"),
                    "status": g.status.value,
                    "realized_return_pct": g.realized_return_pct,
                    "detail": g.detail,
                }
                for g in graded
            ],
            indent=1,
        ),
        encoding="utf-8",
        newline="\n",
    )
    (run_dir / "scores.json").write_text(json.dumps(scores, indent=1), encoding="utf-8", newline="\n")
    store.upsert_run(run_id, case.meta.case_id, config.model_dump_json(), "done",
                     scores_json=json.dumps(scores), suite_id=suite_id)
    return RunResult(run_id, memo, scores, unverified, run_dir)
