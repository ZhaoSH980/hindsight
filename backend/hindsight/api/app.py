"""FastAPI app factory. `app` at module level serves uvicorn:
    backend/.venv/Scripts/python -m uvicorn hindsight.api.app:app --port 8000
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hindsight.api.deps import make_state


def create_app(repo_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Hindsight API")
    app.state.hindsight = make_state(repo_root)
    # runs execute in this process's daemon threads — any row still marked
    # queued/running at startup was orphaned by a previous shutdown
    app.state.hindsight.store.sweep_orphaned_runs()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    from hindsight.api.routes_cases import router as cases_router

    app.include_router(cases_router)

    from hindsight.api.routes_runs import router as runs_router

    app.include_router(runs_router)

    from hindsight.api.routes_eval import router as eval_router

    app.include_router(eval_router)

    dist = app.state.hindsight.root / "frontend" / "dist"
    if dist.exists():
        from fastapi.responses import FileResponse
        from fastapi.staticfiles import StaticFiles

        assets_dir = dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="frontend-assets")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str):
            # Registered AFTER every API router above, so /api/* and the
            # websocket route still win; this only catches client-side
            # routes (e.g. /runs/xyz) so a hard refresh doesn't 404.
            candidate = (dist / full_path).resolve()
            dist_resolved = dist.resolve()
            if (
                full_path
                and candidate.is_file()
                and candidate.is_relative_to(dist_resolved)
            ):
                # top-level static assets Vite copies from public/ (favicon,
                # icons) that don't live under /assets
                return FileResponse(candidate)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
