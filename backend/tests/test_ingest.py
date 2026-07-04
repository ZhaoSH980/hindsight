from datetime import date
from pathlib import Path

import pytest

from hindsight.rag.ingest import load_documents

DOC = """---
title: NVDA Q4 FY2025 earnings recap
source: curated summary (see url)
published_at: 2025-02-27
url: https://example.com/nvda-q4
doc_type: news
---
# NVDA Q4 recap

Data center revenue grew strongly. Blackwell ramp on track.
"""

BAD_DOC_NO_DATE = """---
title: missing date
source: x
---
body
"""


def write(dirpath: Path, name: str, content: str) -> None:
    (dirpath / name).write_text(content, encoding="utf-8")


def test_load_documents_parses_frontmatter(tmp_path):
    write(tmp_path, "nvda_q4.md", DOC)
    docs = load_documents(tmp_path)
    assert len(docs) == 1
    d = docs[0]
    assert d.doc_id == "nvda_q4"
    assert d.title == "NVDA Q4 FY2025 earnings recap"
    assert d.published_at == date(2025, 2, 27)
    assert d.doc_type == "news"
    assert "Blackwell" in d.text


def test_missing_published_at_raises(tmp_path):
    write(tmp_path, "bad.md", BAD_DOC_NO_DATE)
    with pytest.raises(ValueError, match="published_at"):
        load_documents(tmp_path)


def test_documents_sorted_by_id(tmp_path):
    write(tmp_path, "b.md", DOC)
    write(tmp_path, "a.md", DOC)
    docs = load_documents(tmp_path)
    assert [d.doc_id for d in docs] == ["a", "b"]


def test_time_bearing_published_at_rejected(tmp_path):
    doc = DOC.replace("published_at: 2025-02-27", "published_at: 2025-02-27 23:30:00")
    write(tmp_path, "t.md", doc)
    with pytest.raises(ValueError, match="published_at"):
        load_documents(tmp_path)


def test_midnight_datetime_published_at_accepted(tmp_path):
    doc = DOC.replace("published_at: 2025-02-27", "published_at: 2025-02-27 00:00:00")
    write(tmp_path, "m.md", doc)
    docs = load_documents(tmp_path)
    assert docs[0].published_at == date(2025, 2, 27)


def test_case_meta_rejects_unknown_keys():
    from pydantic import ValidationError

    from hindsight.data.models import CaseMeta

    with pytest.raises(ValidationError):
        CaseMeta(
            case_id="c",
            title="t",
            ticker="T",
            as_of=date(2025, 1, 1),
            outcome_window_days=10,
            decription="typo",
        )
