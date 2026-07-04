from fastapi.testclient import TestClient

from hindsight.api.app import create_app


def client_for(root):
    return TestClient(create_app(repo_root=root))


def test_list_cases(api_root):
    client = client_for(api_root)
    r = client.get("/api/cases")
    assert r.status_code == 200
    cases = r.json()
    assert len(cases) == 1
    c = cases[0]
    assert c["case_id"] == "fixture_case"
    assert c["ticker"] == "NVDA"
    assert c["as_of"] == "2025-05-22"
    assert c["n_docs"] == 2


def test_case_bars_full_window(api_root):
    client = client_for(api_root)
    r = client.get("/api/cases/fixture_case/bars")
    assert r.status_code == 200
    payload = r.json()
    assert payload["ticker"] == "NVDA"
    dates = [b["date"] for b in payload["bars"]]
    assert "2025-06-20" in dates  # display endpoint returns the FUTURE too (spec §5)


def test_unknown_case_404(api_root):
    client = client_for(api_root)
    assert client.get("/api/cases/nope/bars").status_code == 404


def test_broken_meta_json_does_not_500_the_list(api_root):
    """A stray case dir with corrupt meta.json must be skipped, not crash
    the whole listing (T2-review carryover resilience note)."""
    broken = api_root / "datasets" / "corrupt_case"
    broken.mkdir()
    (broken / "meta.json").write_text("{not valid json", encoding="utf-8")

    client = client_for(api_root)
    r = client.get("/api/cases")
    assert r.status_code == 200
    cases = r.json()
    # the good fixture case still comes back; the broken one is silently skipped
    assert [c["case_id"] for c in cases] == ["fixture_case"]
