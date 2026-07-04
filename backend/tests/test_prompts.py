from datetime import date

from hindsight.agents import prompts
from hindsight.data.models import CaseMeta


def make_meta():
    return CaseMeta(
        case_id="c",
        title="T",
        ticker="NVDA",
        as_of=date(2025, 5, 22),
        outcome_window_days=40,
        description="desc",
    )


def test_analyst_prompt_names_schema_essentials():
    text = prompts.ANALYST_SYSTEM
    for token in ('"claims"', '"direction"', '"magnitude"', '"volatility"',
                  '"confidence"', '"evidence"', '"horizon_days"',
                  "magnitude semantics:", "volatility semantics:"):
        assert token in text


def test_judge_prompt_names_attribution_enum():
    for token in ("evidence_missing", "misread_evidence", "reasonable_but_wrong"):
        assert token in prompts.JUDGE_SYSTEM


def test_case_brief_carries_asof_and_horizon_cap():
    brief = prompts.case_brief(make_meta())
    assert "2025-05-22" in brief
    assert "40" in brief
    assert "NVDA" in brief
