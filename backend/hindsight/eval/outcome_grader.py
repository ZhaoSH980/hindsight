"""Outcome grader: mechanical claim judgment per spec §3.3 rules 1-6.

Runs deliberately OUTSIDE the time sandbox — evaluation is entitled to
realized data. The boundary is the orchestrator: agents never see this
module's inputs. Pure functions; no LLM, no I/O.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from hindsight.data.models import Bar
from hindsight.schemas import (
    Claim,
    DirectionPrediction,
    GradeStatus,
    MagnitudePrediction,
    VolatilityPrediction,
)

MIN_VOL_SAMPLES = 20
HISTORY_BARS = 252


@dataclass
class GradedClaim:
    claim: Claim
    status: GradeStatus
    realized_return_pct: float | None
    detail: str


def _baseline_index(bars: list[Bar], as_of: date) -> int | None:
    """Rule 1: baseline P0 = last close at or before as_of."""
    idx = None
    for i, b in enumerate(bars):
        if b.date <= as_of:
            idx = i
        else:
            break
    return idx


def _std_log_returns(closes: list[float]) -> float:
    rets = [math.log(b / a) for a, b in zip(closes, closes[1:]) if a > 0]
    if not rets:
        return 0.0
    mean = sum(rets) / len(rets)
    return math.sqrt(sum((r - mean) ** 2 for r in rets) / len(rets))


def _percentile(values: list[float], p: float) -> float:
    xs = sorted(values)
    k = (len(xs) - 1) * p / 100
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def grade_claim(claim: Claim, bars: list[Bar], as_of: date) -> GradedClaim:
    bars = sorted(bars, key=lambda b: b.date)  # defensive: grading correctness must not depend on a caller three modules away keeping bars sorted
    i0 = _baseline_index(bars, as_of)
    if i0 is None:
        return GradedClaim(claim, GradeStatus.ungradable, None, "no baseline bar at or before as_of")
    p0 = bars[i0].close
    hi = i0 + claim.horizon_days  # rule 2: Nth bar after the baseline bar
    if hi >= len(bars):
        return GradedClaim(
            claim,
            GradeStatus.ungradable,
            None,
            f"bars cover {len(bars) - 1 - i0} trading days after as_of; horizon {claim.horizon_days}",
        )
    r = bars[hi].close / p0 - 1
    pct = r * 100
    pred = claim.prediction
    if isinstance(pred, DirectionPrediction):
        # rule 3: at-horizon-end, >= for up, <= -threshold for down.
        # Boundary comparisons use math.isclose first: pct is derived from
        # bars[hi].close / p0 - 1, and binary floats mean an exact-percent
        # baseline (e.g. a 108.0/100 close) can land a few ULPs off the
        # threshold (8.000000000000007 instead of 8.0). Without the
        # tolerance, a claim landing exactly on its stated threshold is
        # spuriously graded a miss depending on rounding direction, which
        # would contradict the ">=" / closed-interval semantics rule 3/4
        # promise. abs_tol=1e-9 pp is far below any real price-derived
        # difference, so it never masks a genuine miss.
        if pred.direction == "up":
            threshold = pred.threshold_pct / 100
            hit = r >= threshold or math.isclose(r, threshold, abs_tol=1e-9)
        else:
            threshold = -pred.threshold_pct / 100
            hit = r <= threshold or math.isclose(r, threshold, abs_tol=1e-9)
        return GradedClaim(
            claim,
            GradeStatus.hit if hit else GradeStatus.miss,
            pct,
            f"horizon-end return {pct:+.2f}% vs {pred.direction} {pred.threshold_pct}%",
        )
    if isinstance(pred, MagnitudePrediction):
        # rule 4: closed interval [low_pct, high_pct] — same float-boundary
        # tolerance as rule 3 (see comment above) applied to both endpoints.
        hit = (pred.low_pct <= pct <= pred.high_pct) or math.isclose(
            pct, pred.low_pct, abs_tol=1e-9
        ) or math.isclose(pct, pred.high_pct, abs_tol=1e-9)
        # NOTE: rule 3 compares in ratio-space, rule 4 in pct-space (100x scale
        # difference in effective tolerance). Verified harmless: real float noise
        # tops out ~3e-14 in ratio space, >1000x below the tighter bound.
        return GradedClaim(
            claim,
            GradeStatus.hit if hit else GradeStatus.miss,
            pct,
            f"horizon-end return {pct:+.2f}% vs [{pred.low_pct}, {pred.high_pct}]",
        )
    assert isinstance(pred, VolatilityPrediction)
    # rule 5: realized window std of log returns vs rolling same-length windows
    window = [b.close for b in bars[i0 : hi + 1]]
    realized = _std_log_returns(window)
    history = [b.close for b in bars[: i0 + 1]][-(HISTORY_BARS + 1) :]
    n = claim.horizon_days
    samples = [
        _std_log_returns(history[j : j + n + 1]) for j in range(len(history) - n)
    ]
    if len(samples) < MIN_VOL_SAMPLES:
        return GradedClaim(claim, GradeStatus.ungradable, pct, "insufficient history for volatility percentile")
    threshold = _percentile(samples, pred.percentile)
    hit = realized > threshold if pred.relation == "above" else realized < threshold
    return GradedClaim(
        claim,
        GradeStatus.hit if hit else GradeStatus.miss,
        pct,
        f"realized vol {realized:.5f} vs p{pred.percentile:g} {threshold:.5f} ({pred.relation})",
    )


def grade_claims(claims: list[Claim], bars: list[Bar], as_of: date) -> list[GradedClaim]:
    return [grade_claim(c, bars, as_of) for c in claims]


_BUCKETS = [(0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]


def aggregate(graded: list[GradedClaim]) -> dict:
    gradable = [g for g in graded if g.status != GradeStatus.ungradable]
    hits = [g for g in gradable if g.status == GradeStatus.hit]
    brier = (
        sum(
            (g.claim.confidence - (1.0 if g.status == GradeStatus.hit else 0.0)) ** 2
            for g in gradable
        )
        / len(gradable)
        if gradable
        else None
    )
    calibration = []
    for lo, hi in _BUCKETS:
        inb = [
            g
            for g in gradable
            if (lo <= g.claim.confidence < hi) or (hi == 1.0 and g.claim.confidence == 1.0)
        ]
        calibration.append(
            {
                "lo": lo,
                "hi": hi,
                "n": len(inb),
                "avg_confidence": sum(g.claim.confidence for g in inb) / len(inb) if inb else None,
                "hit_rate": (
                    sum(1 for g in inb if g.status == GradeStatus.hit) / len(inb) if inb else None
                ),
            }
        )
    return {
        "n_claims": len(graded),
        "n_gradable": len(gradable),
        "n_hit": len(hits),
        "hit_rate": len(hits) / len(gradable) if gradable else None,
        "brier": brier,
        "calibration": calibration,
    }
