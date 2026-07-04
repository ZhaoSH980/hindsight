"""Integrity checks for the real NVDA case dataset (no network)."""
from datetime import date, timedelta
from pathlib import Path

import pytest

from hindsight.data.cases import load_case

CASE_DIR = Path(__file__).resolve().parents[2] / "datasets" / "nvda_fy26q1"

pytestmark = pytest.mark.skipif(
    not (CASE_DIR / "bars.json").exists(), reason="bars not frozen yet"
)


def test_case_loads():
    case = load_case(CASE_DIR)
    assert case.meta.ticker == "NVDA"
    assert case.meta.as_of == date(2025, 5, 22)
    assert len(case.documents) >= 10


def test_corpus_has_pre_and_post_asof_docs():
    case = load_case(CASE_DIR)
    dates = [d.published_at for d in case.documents]
    assert any(dt <= case.meta.as_of for dt in dates)
    assert any(dt > case.meta.as_of for dt in dates), "need the deliberate future doc"


def test_long_document_present():
    case = load_case(CASE_DIR)
    longest = max(len(d.text) for d in case.documents)
    assert longest >= 24000, "10-K MD&A excerpt must be a real long document (~8k tokens)"


def test_bars_cover_outcome_window():
    case = load_case(CASE_DIR)
    bars = case.bars_source.get_bars(
        "NVDA", case.meta.as_of - timedelta(days=1), date(2025, 8, 15)
    )
    post = [b for b in bars if b.date > case.meta.as_of]
    assert len(post) >= case.meta.outcome_window_days
