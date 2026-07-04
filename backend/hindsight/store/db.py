"""SQLite store for run summaries and experience cards.

Thread-safe from birth (check_same_thread=False + lock) because D3's
FastAPI threadpool will share it. Claims and traces are NOT stored here —
run-dir files are authoritative for details (spec §4.3).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    def __init__(self, db_path: Path):
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS runs ("
                " run_id TEXT PRIMARY KEY, case_id TEXT NOT NULL,"
                " suite_id TEXT, config_json TEXT NOT NULL,"
                " status TEXT NOT NULL, scores_json TEXT,"
                " created_at TEXT NOT NULL)"
            )
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS experiences ("
                " exp_id TEXT PRIMARY KEY, source_case_id TEXT NOT NULL,"
                " source_run_id TEXT NOT NULL, as_of TEXT NOT NULL,"
                " outcome_window_end TEXT NOT NULL, features_text TEXT NOT NULL,"
                " card_json TEXT NOT NULL, created_at TEXT NOT NULL)"
            )
            self._conn.commit()

    def upsert_run(
        self,
        run_id: str,
        case_id: str,
        config_json: str,
        status: str,
        scores_json: str | None = None,
        suite_id: str | None = None,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO runs VALUES (?, ?, ?, ?, ?, ?, ?)"
                " ON CONFLICT(run_id) DO UPDATE SET"
                " status=excluded.status, scores_json=excluded.scores_json",
                (run_id, case_id, suite_id, config_json, status, scores_json, now_iso()),
            )
            self._conn.commit()

    def sweep_orphaned_runs(self) -> int:
        """Mark queued/running rows as failed. Runs execute in daemon threads
        of the server process, so after a (re)start any such row is by
        definition an orphan that would otherwise show 'running' forever."""
        note = json.dumps({"status": "crashed", "error": "orphaned by server restart"})
        with self._lock:
            cur = self._conn.execute(
                "UPDATE runs SET status='failed', scores_json=COALESCE(scores_json, ?)"
                " WHERE status IN ('queued', 'running')",
                (note,),
            )
            self._conn.commit()
        return cur.rowcount

    def get_runs(self, suite_id: str | None = None) -> list[dict[str, Any]]:
        with self._lock:
            if suite_id is None:
                rows = self._conn.execute("SELECT * FROM runs ORDER BY created_at").fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM runs WHERE suite_id = ? ORDER BY created_at", (suite_id,)
                ).fetchall()
        return [dict(r) for r in rows]

    def insert_experience(
        self,
        exp_id: str,
        source_case_id: str,
        source_run_id: str,
        as_of: str,
        outcome_window_end: str,
        features_text: str,
        card_json: str,
    ) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO experiences VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    exp_id,
                    source_case_id,
                    source_run_id,
                    as_of,
                    outcome_window_end,
                    features_text,
                    card_json,
                    now_iso(),
                ),
            )
            self._conn.commit()

    def query_experiences(
        self,
        as_of: str,
        exclude_case_id: str,
        created_before: str | None = None,
    ) -> list[dict[str, Any]]:
        """Time-gated candidates (spec §3.5): window closed by as_of, never the
        same case, optionally only cards existing before a suite snapshot."""
        sql = (
            "SELECT * FROM experiences"
            " WHERE outcome_window_end <= ? AND source_case_id != ?"
        )
        params: list[Any] = [as_of, exclude_case_id]
        if created_before is not None:
            sql += " AND created_at < ?"
            params.append(created_before)
        with self._lock:
            rows = self._conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
