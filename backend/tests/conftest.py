import json
from pathlib import Path

import pytest

META = {
    "case_id": "fixture_case",
    "title": "Fixture case",
    "ticker": "NVDA",
    "as_of": "2025-05-22",
    "outcome_window_days": 20,
    "description": "test fixture",
    "tags": ["test"],
}

BARS = {
    "ticker": "NVDA",
    "auto_adjust": True,
    "fetched_at": "x",
    "bars": [
        {"date": "2025-05-20", "open": 1, "high": 1, "low": 1, "close": 1.0, "volume": 1},
        {"date": "2025-05-21", "open": 1, "high": 1, "low": 1, "close": 1.1, "volume": 1},
        {"date": "2025-05-22", "open": 1, "high": 1, "low": 1, "close": 1.2, "volume": 1},
        {"date": "2025-06-20", "open": 1, "high": 1, "low": 1, "close": 2.0, "volume": 1},
    ],
}

DOC_PAST = """---
title: pre-earnings guidance note
source: fixture
published_at: 2025-05-01
doc_type: news
---
nvidia guidance strong, data center demand robust
"""

DOC_FUTURE = """---
title: post-earnings recap
source: fixture
published_at: 2025-05-28
doc_type: news
---
nvidia earnings smashed records
"""


@pytest.fixture
def case_dir(tmp_path) -> Path:
    d = tmp_path / "fixture_case"
    (d / "docs").mkdir(parents=True)
    (d / "meta.json").write_text(json.dumps(META), encoding="utf-8")
    (d / "bars.json").write_text(json.dumps(BARS), encoding="utf-8")
    (d / "docs" / "past.md").write_text(DOC_PAST, encoding="utf-8")
    (d / "docs" / "future.md").write_text(DOC_FUTURE, encoding="utf-8")
    return d


@pytest.fixture
def api_root(case_dir, tmp_path) -> Path:
    """A fake repo root: datasets/<case>, empty runs/, fresh hindsight.db."""
    import shutil

    root = tmp_path / "approot"
    (root / "datasets").mkdir(parents=True)
    shutil.copytree(case_dir, root / "datasets" / case_dir.name)
    (root / "runs").mkdir()
    return root
