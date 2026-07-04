from datetime import date

from hindsight.data.cases import load_case


def test_load_case_builds_everything(case_dir):
    case = load_case(case_dir)
    assert case.meta.case_id == "fixture_case"
    assert case.meta.as_of == date(2025, 5, 22)
    assert len(case.documents) == 2
    assert len(case.chunks) >= 2
    bars = case.bars_source.get_bars("NVDA", date(2025, 5, 20), date(2025, 5, 22))
    assert len(bars) == 3


def test_dry_run_smoke(case_dir, capsys):
    from hindsight.cli import dry_run

    dry_run(case_dir, query="nvidia guidance")
    out = capsys.readouterr().out
    assert "corpus_search" in out
    assert "DENIED lookahead" in out
    assert "post-earnings recap" not in out  # future doc never surfaces
