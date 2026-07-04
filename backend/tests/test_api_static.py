"""SPA fallback + static asset serving (T2-review carryover).

StaticFiles(html=True) mounted at "/" would swallow every path, including
/api/*, if it were registered before the API routers -- and even registered
after, a naive catch-all conflicts with a plain "/" mount. The app instead
mounts only /assets for the Vite build's hashed bundle and serves
index.html via a catch-all route registered after every API router, so:
  - /api/* and the websocket route always win (declared first)
  - any other path (a client-side route like /runs/xyz, or a hard refresh)
    gets index.html back instead of a 404
  - a real static file that exists in dist/ (e.g. a public/ asset copied to
    the dist root) is served as itself, not masked by the SPA shell
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from hindsight.api.app import create_app


def make_dist(root):
    dist = root / "frontend" / "dist"
    (dist / "assets").mkdir(parents=True)
    dist_index_html = "<html><body>hindsight-spa-shell</body></html>"
    (dist / "index.html").write_text(dist_index_html, encoding="utf-8")
    (dist / "assets" / "index.abcd1234.js").write_text(
        "console.log('bundle');", encoding="utf-8"
    )
    (dist / "favicon.svg").write_text("<svg></svg>", encoding="utf-8")
    return dist


def test_api_still_resolves_with_dist_present(api_root):
    make_dist(api_root)
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/api/cases")
    assert r.status_code == 200
    assert r.json()[0]["case_id"] == "fixture_case"


def test_client_route_returns_index_html(api_root):
    make_dist(api_root)
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/runs/anything")
    assert r.status_code == 200
    assert "hindsight-spa-shell" in r.text
    assert r.headers["content-type"].startswith("text/html")


def test_root_returns_index_html(api_root):
    make_dist(api_root)
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/")
    assert r.status_code == 200
    assert "hindsight-spa-shell" in r.text


def test_hashed_asset_served_from_assets_mount(api_root):
    make_dist(api_root)
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/assets/index.abcd1234.js")
    assert r.status_code == 200
    assert "bundle" in r.text


def test_top_level_public_asset_served_as_itself(api_root):
    """favicon.svg is copied to the dist root by Vite (from public/), not
    under /assets -- the catch-all must serve it as a file, not index.html."""
    make_dist(api_root)
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/favicon.svg")
    assert r.status_code == 200
    assert "<svg" in r.text
    assert "hindsight-spa-shell" not in r.text


def test_no_dist_means_no_static_routes_and_api_404_still_works(api_root):
    """Without a built frontend (the common dev/test case), there is no
    catch-all at all -- unmatched paths fall through to FastAPI's normal 404."""
    client = TestClient(create_app(repo_root=api_root))
    r = client.get("/runs/anything")
    assert r.status_code == 404
