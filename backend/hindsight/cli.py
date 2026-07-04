"""CLI dry-run: exercise sandbox + retrieval + market data with no LLM.

Usage (from repo root):
    backend/.venv/Scripts/python -m hindsight.cli dry-run \
        --case datasets/nvda_fy26q1 --query "data center demand"
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

from hindsight.data.cases import load_case
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.errors import LookaheadError
from hindsight.sandbox.gate import SandboxedCorpus, SandboxedMarketData

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _anchor(p: str) -> Path:
    """Resolve relative CLI paths against the repo root, not the CWD."""
    path = Path(p)
    return path if path.is_absolute() else _REPO_ROOT / path


def dry_run(case_dir: Path, query: str) -> None:
    case = load_case(case_dir)
    as_of = case.meta.as_of
    audit = AuditLog()
    corpus = SandboxedCorpus(BM25Retriever(case.chunks), as_of=as_of, audit=audit)
    market = SandboxedMarketData(case.bars_source, as_of=as_of, audit=audit)

    print(f"== case {case.meta.case_id} | ticker {case.meta.ticker} | as_of {as_of} ==")
    print(f"\n-- corpus_search: {query!r}")
    for s in corpus.search(query, top_k=5):
        print(f"  [{s.score:6.2f}] {s.chunk.chunk_id}  ({s.chunk.published_at})  {s.chunk.title}")

    print("\n-- price_history (30 calendar days up to as_of)")
    bars = market.get_bars(case.meta.ticker, as_of - timedelta(days=30), as_of)
    if bars:
        pct = (bars[-1].close / bars[0].close - 1) * 100
        print(f"  {len(bars)} bars, window return {pct:+.2f}%, last close {bars[-1].close:.2f}")

    print("\n-- attempting lookahead (should be DENIED)")
    try:
        market.get_bars(case.meta.ticker, as_of, as_of + timedelta(days=30))
    except LookaheadError as exc:
        print(f"  blocked: {exc}")

    print("\n-- audit log")
    for e in audit.as_dicts():
        print(f"  {json.dumps(e, ensure_ascii=False)}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(prog="hindsight")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("dry-run", help="sandboxed retrieval + market data, no LLM")
    p.add_argument("--case", required=True, help="path to datasets/<case_id>")
    p.add_argument("--query", default="latest guidance and demand outlook")

    pr = sub.add_parser("run", help="full research run against a case")
    pr.add_argument("--case", required=True)
    pr.add_argument("--memory", action="store_true")
    pr.add_argument("--max-steps", type=int, default=8)
    pr.add_argument("--runs-root", default="runs")
    pr.add_argument("--db", default="hindsight.db")
    pr.add_argument("--offline", action="store_true")

    args = ap.parse_args()
    if args.command == "dry-run":
        dry_run(_anchor(args.case), args.query)
    if args.command == "run":
        from hindsight.agents.orchestrator import run_research
        from hindsight.llm.client import LLMConfig, openai_transport
        from hindsight.llm.recording import RecordingLLMClient
        from hindsight.llm.retry import with_retry
        from hindsight.schemas import RunConfig
        from hindsight.store.db import Store

        cfg = LLMConfig.from_env()
        llm = RecordingLLMClient(
            transport=with_retry(openai_transport(cfg)),
            db_path=_anchor("llm_calls.sqlite"),
            model=cfg.model,
            offline=True if args.offline else None,
        )
        result = run_research(
            case_dir=_anchor(args.case),
            config=RunConfig(model=cfg.model, memory_on=args.memory, max_steps=args.max_steps),
            llm=llm,
            store=Store(_anchor(args.db)),
            runs_root=_anchor(args.runs_root),
        )
        print(f"run {result.run_id} -> {result.run_dir}")
        print(json.dumps(result.scores, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
