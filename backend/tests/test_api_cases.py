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
