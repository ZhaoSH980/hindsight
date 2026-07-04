import math
from datetime import date, timedelta

from hindsight.data.models import Bar
from hindsight.eval.outcome_grader import GradedClaim, aggregate, grade_claim
from hindsight.schemas import Claim, ClaimType, GradeStatus


def make_bars(closes: list[float], start: date = date(2025, 5, 1)) -> list[Bar]:
    return [
        Bar(date=start + timedelta(days=i), open=c, high=c, low=c, close=c, volume=1)
        for i, c in enumerate(closes)
    ]


def direction_claim(threshold=5.0, horizon=2, direction="up", confidence=0.7):
    return Claim(
        claim_id="c1",
        statement="s",
        type=ClaimType.direction,
        ticker="NVDA",
        horizon_days=horizon,
        prediction={"direction": direction, "threshold_pct": threshold},
        confidence=confidence,
        evidence=["e::000"],
    )


AS_OF = date(2025, 5, 3)  # bars[2] is the baseline (start + 2 days)


def test_direction_up_hit_at_exact_threshold():
    bars = make_bars([100, 100, 100, 102, 105.0])  # baseline 100, horizon 2 -> 105
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.hit  # r == threshold -> hit (rule 3: >=)
    assert math.isclose(g.realized_return_pct, 5.0)


def test_direction_up_miss_below_threshold():
    bars = make_bars([100, 100, 100, 102, 104.9])
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.miss


def test_direction_down_hit():
    bars = make_bars([100, 100, 100, 96, 94.0])
    g = grade_claim(direction_claim(direction="down", threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.hit


def test_at_horizon_end_not_path_touch():
    # touches +6% intraday path at bar 3 but ends at +1% -> miss (rule 3)
    bars = make_bars([100, 100, 100, 106, 101.0])
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.miss


def test_nontrading_asof_uses_prior_close():
    bars = make_bars([100, 100, 100, 102, 105.0])
    weekend = AS_OF + timedelta(hours=0)  # same day; simulate gap by removing bar
    bars_gap = [b for b in bars if b.date != AS_OF]  # as_of date itself has no bar
    g = grade_claim(direction_claim(threshold=5.0, horizon=2), bars_gap, AS_OF)
    # baseline falls back to bars[1] (100); horizon counts bars after it: 102 then 105
    assert g.status == GradeStatus.hit


def test_horizon_beyond_data_is_ungradable():
    bars = make_bars([100, 100, 100, 102])
    g = grade_claim(direction_claim(horizon=5), bars, AS_OF)
    assert g.status == GradeStatus.ungradable


def test_no_baseline_is_ungradable():
    bars = make_bars([100, 100], start=date(2025, 6, 1))  # all after as_of
    g = grade_claim(direction_claim(), bars, AS_OF)
    assert g.status == GradeStatus.ungradable


def test_magnitude_interval_closed_endpoints():
    bars = make_bars([100, 100, 100, 102, 108.0])
    claim = Claim(
        claim_id="m1", statement="s", type=ClaimType.magnitude, ticker="NVDA",
        horizon_days=2, prediction={"low_pct": 2.0, "high_pct": 8.0},
        confidence=0.5, evidence=["e::000"],
    )
    assert grade_claim(claim, bars, AS_OF).status == GradeStatus.hit  # 8.0 == high -> hit
    bars_out = make_bars([100, 100, 100, 102, 108.1])
    assert grade_claim(claim, bars_out, AS_OF).status == GradeStatus.miss


def test_split_adjusted_series_grades_smoothly():
    # A 10:1 split inside the outcome window: the frozen snapshot is
    # auto-adjusted so closes are continuous — grading must NOT see -90%.
    bars = make_bars([100, 100, 100, 101, 103.0])  # adjusted series, split invisible
    g = grade_claim(direction_claim(threshold=2.0, horizon=2), bars, AS_OF)
    assert g.status == GradeStatus.hit
    assert g.realized_return_pct > 0


def test_volatility_above_hits_in_high_vol_window():
    import random

    rng = random.Random(7)
    quiet = [100.0]
    for _ in range(300):
        quiet.append(quiet[-1] * (1 + rng.uniform(-0.002, 0.002)))
    wild = [quiet[-1]]
    for _ in range(10):
        wild.append(wild[-1] * (1 + rng.uniform(-0.08, 0.08)))
    closes = quiet + wild[1:]
    bars = make_bars(closes, start=date(2024, 6, 1))
    as_of = bars[300].date
    claim = Claim(
        claim_id="v1", statement="s", type=ClaimType.volatility, ticker="NVDA",
        horizon_days=10, prediction={"relation": "above", "percentile": 90},
        confidence=0.6, evidence=["e::000"],
    )
    assert grade_claim(claim, bars, as_of).status == GradeStatus.hit


def test_volatility_insufficient_history_ungradable():
    bars = make_bars([100.0] * 15)
    claim = Claim(
        claim_id="v1", statement="s", type=ClaimType.volatility, ticker="NVDA",
        horizon_days=3, prediction={"relation": "above", "percentile": 80},
        confidence=0.6, evidence=["e::000"],
    )
    assert grade_claim(claim, bars, bars[5].date).status == GradeStatus.ungradable


def test_aggregate_brier_and_calibration():
    graded = [
        GradedClaim(direction_claim(confidence=0.9), GradeStatus.hit, 6.0, ""),
        GradedClaim(direction_claim(confidence=0.9), GradeStatus.miss, 1.0, ""),
        GradedClaim(direction_claim(confidence=0.1), GradeStatus.miss, -1.0, ""),
        GradedClaim(direction_claim(confidence=0.5), GradeStatus.ungradable, None, ""),
    ]
    agg = aggregate(graded)
    assert agg["n_claims"] == 4
    assert agg["n_gradable"] == 3
    assert math.isclose(agg["hit_rate"], 1 / 3)
    expected_brier = ((0.9 - 1) ** 2 + (0.9 - 0) ** 2 + (0.1 - 0) ** 2) / 3
    assert math.isclose(agg["brier"], expected_brier)
    buckets = {(b["lo"], b["hi"]): b for b in agg["calibration"]}
    assert buckets[(0.8, 1.0)]["n"] == 2
    assert math.isclose(buckets[(0.8, 1.0)]["hit_rate"], 0.5)


def test_shuffled_bars_grade_identically():
    import random as _random

    bars = make_bars([100, 100, 100, 102, 105.0])
    shuffled = bars[:]
    # seed 0, not 3: seed 3's permutation [0,2,3,4,1] happens to reproduce the
    # correct grade even without sorting (baseline still hits a 100-close and
    # horizon+2 still lands on 105.0); seed 0's [2,1,0,4,3] genuinely diverges
    # (miss/2.0 vs hit/5.0), so only seed 0 actually locks the defensive sort.
    _random.Random(0).shuffle(shuffled)
    a = grade_claim(direction_claim(threshold=5.0, horizon=2), bars, AS_OF)
    b = grade_claim(direction_claim(threshold=5.0, horizon=2), shuffled, AS_OF)
    assert (a.status, a.realized_return_pct) == (b.status, b.realized_return_pct)


def test_percentile_linear_interpolation():
    from hindsight.eval.outcome_grader import _percentile

    values = [4.0, 1.0, 3.0, 2.0]
    assert _percentile(values, 0) == 1.0
    assert _percentile(values, 100) == 4.0
    assert _percentile(values, 50) == 2.5
    assert _percentile(values, 25) == 1.75
