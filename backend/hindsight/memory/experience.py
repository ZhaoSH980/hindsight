"""Experience library: cross-run Reflexion with a time gate (spec §3.5).

Write-always; RunConfig.memory_on gates READS only. Retrieval enforces
three hard constraints (in SQL, Store.query_experiences): the source run's
outcome window closed at or before the new run's as_of; never the same
case (leave-one-out); optionally only cards existing before a suite
snapshot. BM25 ranking happens only over candidates that pass the gate.
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from hindsight.data.models import CaseMeta
from hindsight.eval.judge import JudgeReport
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.rag.bm25_retriever import _tokenize
from hindsight.schemas import GradeStatus
from hindsight.store.db import Store

from rank_bm25 import BM25Okapi


class ExperienceCard(BaseModel):
    model_config = ConfigDict(extra="forbid")
    exp_id: str
    source_case_id: str
    source_run_id: str
    as_of: date
    outcome_window_end: date
    features_text: str
    strategy_summary: str
    outcomes: dict[str, Any]
    lesson_attribution: str | None = None
    lesson_text: str = ""


def build_card(
    case: CaseMeta,
    run_id: str,
    graded: list[GradedClaim],
    report: JudgeReport | None,
    outcome_window_end: date,
) -> ExperienceCard:
    outcomes = {
        g.claim.claim_id: {
            "status": g.status.value,
            "statement": g.claim.statement,
            "confidence": g.claim.confidence,
        }
        for g in graded
    }
    misses = [g for g in graded if g.status == GradeStatus.miss]
    attribution: str | None = None
    if misses and report is not None and report.attributions:
        counts = Counter(a.attribution for a in report.attributions)
        attribution = counts.most_common(1)[0][0]
    if not misses:
        lesson = "Calibration held: graded claims came true at the stated confidence."
    elif attribution:
        lesson = f"Missed claims were mostly {attribution}; adjust research accordingly."
    else:
        lesson = "Claims missed; no attribution available."
    return ExperienceCard(
        exp_id=f"exp_{run_id}",
        source_case_id=case.case_id,
        source_run_id=run_id,
        as_of=case.as_of,
        outcome_window_end=outcome_window_end,
        features_text=f"{case.ticker} {' '.join(case.tags)} {case.title}",
        strategy_summary=f"{len(graded)} claims, "
        f"{sum(1 for g in graded if g.status == GradeStatus.hit)} hit",
        outcomes=outcomes,
        lesson_attribution=attribution,
        lesson_text=lesson,
    )


class ExperienceRetriever:
    def __init__(self, store: Store):
        self._store = store

    def write(self, card: ExperienceCard) -> None:
        self._store.insert_experience(
            card.exp_id,
            card.source_case_id,
            card.source_run_id,
            card.as_of.isoformat(),
            card.outcome_window_end.isoformat(),
            card.features_text,
            card.model_dump_json(),
        )

    def retrieve(
        self,
        features_text: str,
        as_of: date,
        exclude_case_id: str,
        created_before: str | None = None,
        top_k: int = 3,
    ) -> list[ExperienceCard]:
        rows = self._store.query_experiences(
            as_of.isoformat(), exclude_case_id, created_before
        )
        if not rows:
            return []
        cards = [ExperienceCard(**json.loads(r["card_json"])) for r in rows]
        index = BM25Okapi([_tokenize(c.features_text) for c in cards])
        scores = index.get_scores(_tokenize(features_text))
        ranked = sorted(zip(cards, scores), key=lambda p: p[1], reverse=True)
        return [c for c, _ in ranked[: max(1, top_k)]]


def render_cards(cards: list[ExperienceCard]) -> str:
    blocks = []
    for c in cards:
        hits = sum(1 for o in c.outcomes.values() if o.get("status") == "hit")
        blocks.append(
            f"- [{c.source_case_id}] {c.features_text} — {c.strategy_summary} "
            f"({hits}/{len(c.outcomes)} claims hit). Lesson"
            + (f" ({c.lesson_attribution})" if c.lesson_attribution else "")
            + f": {c.lesson_text}"
        )
    return "\n".join(blocks)
