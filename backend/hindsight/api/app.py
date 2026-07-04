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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    from hindsight.api.routes_cases import router as cases_router

    app.include_router(cases_router)

    dist = app.state.hindsight.root / "frontend" / "dist"
    if dist.exists():
        from fastapi.staticfiles import StaticFiles

        app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
    return app


app = create_app()
