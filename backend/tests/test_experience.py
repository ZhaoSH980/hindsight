import json
from datetime import date

from hindsight.data.models import CaseMeta
from hindsight.eval.judge import Attribution, ClaimGrounding, JudgeReport
from hindsight.eval.outcome_grader import GradedClaim
from hindsight.memory.experience import (
    ExperienceCard,
    ExperienceRetriever,
    build_card,
    render_cards,
)
from hindsight.schemas import Claim, ClaimType, GradeStatus
from hindsight.store.db import Store


def make_graded(status=GradeStatus.miss):
    claim = Claim(
        claim_id="c1", statement="NVDA up 5% in 20d", type=ClaimType.direction,
        ticker="NVDA", horizon_days=20,
        prediction={"direction": "up", "threshold_pct": 5.0},
        confidence=0.8, evidence=["a::000"],
    )
    return GradedClaim(claim, status, -2.0 if status == GradeStatus.miss else 6.0, "d")


def make_report():
    return JudgeReport(
        grounding=[ClaimGrounding(claim_id="c1", supported=True)],
        reasoning_consistency=4,
        retrieval_sufficiency=3,
        attributions=[Attribution(claim_id="c1", attribution="misread_evidence")],
    )


META = CaseMeta(
    case_id="case_a", title="NVDA earnings", ticker="NVDA",
    as_of=date(2025, 3, 1), outcome_window_days=20, tags=["earnings"],
)


def test_build_card_carries_lesson_and_window():
    card = build_card(META, "r1", [make_graded()], make_report(), date(2025, 4, 15))
    assert card.source_case_id == "case_a"
    assert card.outcome_window_end == date(2025, 4, 15)
    assert card.lesson_attribution == "misread_evidence"
    assert "NVDA" in card.features_text
    assert card.outcomes["c1"]["status"] == "miss"


def test_build_card_all_hits_lesson():
    card = build_card(
        META, "r1", [make_graded(GradeStatus.hit)], make_report(), date(2025, 4, 15)
    )
    assert card.lesson_attribution is None
    assert "held" in card.lesson_text


def test_retriever_ranks_by_similarity(tmp_path):
    store = Store(tmp_path / "h.db")
    r = ExperienceRetriever(store)
    for i, (case_id, feats) in enumerate(
        [("c_nvda", "NVDA earnings semis ai-capex"),
         ("c_tsla", "TSLA delivery autos"),
         ("c_smci", "SMCI filing servers")]
    ):
        card = build_card(
            CaseMeta(case_id=case_id, title=feats, ticker=feats.split()[0],
                     as_of=date(2025, 1, 1), outcome_window_days=5),
            f"r{i}", [make_graded()], make_report(), date(2025, 2, 1),
        )
        r.write(card)
    got = r.retrieve("NVDA earnings ai", as_of=date(2025, 5, 22),
                     exclude_case_id="other", top_k=1)
    assert got[0].source_case_id == "c_nvda"


def test_render_cards_mentions_lesson(tmp_path):
    card = build_card(META, "r1", [make_graded()], make_report(), date(2025, 4, 15))
    text = render_cards([card])
    assert "misread_evidence" in text
    assert "NVDA" in text
