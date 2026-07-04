from datetime import date

import pytest
from pydantic import ValidationError

from hindsight.schemas import (
    Claim,
    ClaimType,
    DirectionPrediction,
    GradeStatus,
    MagnitudePrediction,
    Memo,
    RunConfig,
    VolatilityPrediction,
)


def make_claim(**over):
    base = dict(
        claim_id="c1",
        statement="NVDA closes >=5% above the as_of price on the 20th trading day",
        type=ClaimType.direction,
        ticker="NVDA",
        horizon_days=20,
        prediction={"direction": "up", "threshold_pct": 5.0},
        confidence=0.72,
        evidence=["chunk_001"],
    )
    base.update(over)
    return Claim(**base)


def test_direction_claim_valid():
    c = make_claim()
    assert isinstance(c.prediction, DirectionPrediction)
    assert c.prediction.threshold_pct == 5.0


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        make_claim(confidence=1.5)
    with pytest.raises(ValidationError):
        make_claim(confidence=-0.1)


def test_evidence_must_be_nonempty():
    with pytest.raises(ValidationError):
        make_claim(evidence=[])


def test_prediction_must_match_type():
    with pytest.raises(ValidationError):
        make_claim(
            type=ClaimType.magnitude,
            prediction={"direction": "up", "threshold_pct": 5.0},
        )


def test_magnitude_interval_ordered():
    c = make_claim(
        type=ClaimType.magnitude,
        prediction={"low_pct": -2.0, "high_pct": 8.0},
    )
    assert isinstance(c.prediction, MagnitudePrediction)
    with pytest.raises(ValidationError):
        make_claim(
            type=ClaimType.magnitude,
            prediction={"low_pct": 8.0, "high_pct": -2.0},
        )


def test_volatility_percentile_bounds():
    c = make_claim(
        type=ClaimType.volatility,
        prediction={"relation": "above", "percentile": 80},
    )
    assert isinstance(c.prediction, VolatilityPrediction)
    with pytest.raises(ValidationError):
        make_claim(
            type=ClaimType.volatility,
            prediction={"relation": "above", "percentile": 101},
        )


def test_memo_requires_claims():
    with pytest.raises(ValidationError):
        Memo(background="b", bull_case="+", bear_case="-", conclusion="c", claims=[])


def test_runconfig_defaults():
    cfg = RunConfig()
    assert cfg.max_steps == 8
    assert cfg.memory_on is False
    assert cfg.context_budget == 8000
    assert cfg.retrieval_top_k == 5


def test_grade_status_values():
    assert {s.value for s in GradeStatus} == {"hit", "miss", "ungradable"}
