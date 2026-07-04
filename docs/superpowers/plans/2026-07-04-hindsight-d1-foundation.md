# Hindsight D1 — Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the D1 foundation of Hindsight: Pydantic schemas, time sandbox with audit + leakage tests, market/corpus data layer with time-filtered BM25 retrieval, tool registry, trace recorder, LLM record/replay client, endpoint probe, CLI dry-run, and the first (NVDA) case dataset — everything except the agents themselves.

**Architecture:** Pure-Python backend package `hindsight` under `backend/`. All data access flows through sandbox wrappers that enforce `as_of` gating and write audit entries. LLM calls flow through a recording client keyed by request hash (SQLite), enabling offline replay. No agent/LLM logic in D1 — the CLI dry-run exercises retrieval + market data + sandbox without any LLM call.

**Tech Stack:** Python ≥3.11 (dev on 3.13), Pydantic v2, rank-bm25, yfinance (`auto_adjust=True`), python-frontmatter, openai SDK (OpenAI-compatible endpoint), python-dotenv, pytest, GitHub Actions.

**Working directory:** all commands run from the repo root `F:/AIProjects/my_show/hindsight` unless stated. Backend venv lives at `backend/.venv`; on Windows Git Bash the interpreter is `backend/.venv/Scripts/python`.

**Reference spec:** `docs/superpowers/specs/2026-07-04-hindsight-design.md` (§3.2 sandbox, §3.3 claim semantics, §4 data design, §9 tests, §10 D1).

---

### Task 1: Backend scaffold, venv, pytest smoke test, CI

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/hindsight/__init__.py`
- Create: `backend/tests/test_smoke.py`
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Write `backend/pyproject.toml`**

```toml
[project]
name = "hindsight"
version = "0.1.0"
description = "Time-travel evaluation harness for deep research agents"
requires-python = ">=3.11"
dependencies = [
    "pydantic>=2.7",
    "rank-bm25>=0.2.2",
    "yfinance>=0.2.40",
    "python-frontmatter>=1.1",
    "openai>=1.30",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8"]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["hindsight*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Create package and smoke test**

`backend/hindsight/__init__.py`:

```python
__version__ = "0.1.0"
```

`backend/tests/test_smoke.py`:

```python
import hindsight


def test_package_imports():
    assert hindsight.__version__ == "0.1.0"
```

- [ ] **Step 3: Create venv and install**

Run: `cd backend && python -m venv .venv && .venv/Scripts/python -m pip install -q -e ".[dev]"`
Expected: exits 0 (takes a couple of minutes; yfinance pulls pandas).

- [ ] **Step 4: Run smoke test**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: `1 passed`

- [ ] **Step 5: Write `.github/workflows/ci.yml`**

```yaml
name: ci
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e "backend[dev]"
      - run: cd backend && pytest -q
```

- [ ] **Step 6: Commit**

```bash
git add backend .github
git commit -m "feat(d1): backend scaffold, pytest, CI"
```

---

### Task 2: Domain schemas (`schemas.py`)

Implements spec §3.3 (claim schema + validation rules used by Critic layer ①).

**Files:**
- Create: `backend/hindsight/schemas.py`
- Test: `backend/tests/test_schemas.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_schemas.py`:

```python
from datetime import date

import pytest
from pydantic import ValidationError

from hindsight.schemas import (
    Claim,
    ClaimType,
    DirectionPrediction,
    GradeStatus,
    MagnitudePrediction,
    Memo,
    RunConfig,
    VolatilityPrediction,
)


def make_claim(**over):
    base = dict(
        claim_id="c1",
        statement="NVDA closes >=5% above the as_of price on the 20th trading day",
        type=ClaimType.direction,
        ticker="NVDA",
        horizon_days=20,
        prediction={"direction": "up", "threshold_pct": 5.0},
        confidence=0.72,
        evidence=["chunk_001"],
    )
    base.update(over)
    return Claim(**base)


def test_direction_claim_valid():
    c = make_claim()
    assert isinstance(c.prediction, DirectionPrediction)
    assert c.prediction.threshold_pct == 5.0


def test_confidence_bounds():
    with pytest.raises(ValidationError):
        make_claim(confidence=1.5)
    with pytest.raises(ValidationError):
        make_claim(confidence=-0.1)


def test_evidence_must_be_nonempty():
    with pytest.raises(ValidationError):
        make_claim(evidence=[])


def test_prediction_must_match_type():
    with pytest.raises(ValidationError):
        make_claim(
            type=ClaimType.magnitude,
            prediction={"direction": "up", "threshold_pct": 5.0},
        )


def test_magnitude_interval_ordered():
    c = make_claim(
        type=ClaimType.magnitude,
        prediction={"low_pct": -2.0, "high_pct": 8.0},
    )
    assert isinstance(c.prediction, MagnitudePrediction)
    with pytest.raises(ValidationError):
        make_claim(
            type=ClaimType.magnitude,
            prediction={"low_pct": 8.0, "high_pct": -2.0},
        )


def test_volatility_percentile_bounds():
    c = make_claim(
        type=ClaimType.volatility,
        prediction={"relation": "above", "percentile": 80},
    )
    assert isinstance(c.prediction, VolatilityPrediction)
    with pytest.raises(ValidationError):
        make_claim(
            type=ClaimType.volatility,
            prediction={"relation": "above", "percentile": 101},
        )


def test_memo_requires_claims():
    with pytest.raises(ValidationError):
        Memo(background="b", bull_case="+", bear_case="-", conclusion="c", claims=[])


def test_runconfig_defaults():
    cfg = RunConfig()
    assert cfg.max_steps == 8
    assert cfg.memory_on is False
    assert cfg.context_budget == 8000
    assert cfg.retrieval_top_k == 5


def test_grade_status_values():
    assert {s.value for s in GradeStatus} == {"hit", "miss", "ungradable"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_schemas.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'hindsight.schemas'`

- [ ] **Step 3: Write `backend/hindsight/schemas.py`**

```python
"""Domain schemas: claims, memo, run config. Spec §3.3."""
from __future__ import annotations

from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field, model_validator


class ClaimType(str, Enum):
    direction = "direction"
    magnitude = "magnitude"
    volatility = "volatility"


class GradeStatus(str, Enum):
    hit = "hit"
    miss = "miss"
    ungradable = "ungradable"


class DirectionPrediction(BaseModel):
    direction: Literal["up", "down"]
    threshold_pct: float = Field(gt=0)


class MagnitudePrediction(BaseModel):
    low_pct: float
    high_pct: float

    @model_validator(mode="after")
    def _ordered(self) -> "MagnitudePrediction":
        if self.low_pct > self.high_pct:
            raise ValueError("low_pct must be <= high_pct")
        return self


class VolatilityPrediction(BaseModel):
    relation: Literal["above", "below"]
    percentile: float = Field(ge=0, le=100)


Prediction = Union[DirectionPrediction, MagnitudePrediction, VolatilityPrediction]

_PREDICTION_FOR_TYPE = {
    ClaimType.direction: DirectionPrediction,
    ClaimType.magnitude: MagnitudePrediction,
    ClaimType.volatility: VolatilityPrediction,
}


class Claim(BaseModel):
    claim_id: str
    statement: str
    type: ClaimType
    ticker: str
    horizon_days: int = Field(gt=0)
    prediction: Prediction
    confidence: float = Field(ge=0, le=1)
    evidence: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def _prediction_matches_type(self) -> "Claim":
        expected = _PREDICTION_FOR_TYPE[self.type]
        if not isinstance(self.prediction, expected):
            raise ValueError(
                f"claim type {self.type.value} requires {expected.__name__}, "
                f"got {type(self.prediction).__name__}"
            )
        return self


class Memo(BaseModel):
    background: str
    bull_case: str
    bear_case: str
    conclusion: str
    claims: list[Claim] = Field(min_length=1)


class RunConfig(BaseModel):
    model: str = ""
    temperature: float = 0.2
    max_steps: int = Field(default=8, gt=0)
    memory_on: bool = False
    context_budget: int = Field(default=8000, gt=0)
    retrieval_top_k: int = Field(default=5, gt=0)
```

Note: pydantic resolves the `Prediction` union by trying members in order; `DirectionPrediction`, `MagnitudePrediction`, and `VolatilityPrediction` have disjoint required fields, so there is no ambiguity. The `_prediction_matches_type` validator is the layer-①-check the Critic relies on.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_schemas.py -q`
Expected: `9 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/schemas.py backend/tests/test_schemas.py
git commit -m "feat(d1): domain schemas with claim/prediction validation"
```

---

### Task 3: Data models + document ingest (frontmatter)

Implements spec §4.1 corpus format / §4.2 ingest.

**Files:**
- Create: `backend/hindsight/data/__init__.py` (empty)
- Create: `backend/hindsight/data/models.py`
- Create: `backend/hindsight/rag/__init__.py` (empty)
- Create: `backend/hindsight/rag/ingest.py`
- Test: `backend/tests/test_ingest.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_ingest.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_ingest.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/data/models.py`**

```python
"""Core data records shared across the backend."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class Bar(BaseModel):
    """One daily OHLCV bar. Prices are split/dividend adjusted (auto_adjust=True)."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


class CaseMeta(BaseModel):
    case_id: str
    title: str
    ticker: str
    as_of: date
    outcome_window_days: int = Field(gt=0)
    description: str = ""
    tags: list[str] = Field(default_factory=list)


class Document(BaseModel):
    doc_id: str
    title: str
    source: str
    published_at: date
    url: str = ""
    doc_type: str = "news"
    text: str


class Chunk(BaseModel):
    chunk_id: str
    doc_id: str
    title: str
    published_at: date
    text: str


class ScoredChunk(BaseModel):
    chunk: Chunk
    score: float
```

- [ ] **Step 4: Write `backend/hindsight/rag/ingest.py`**

```python
"""Load markdown documents with YAML frontmatter into Document records."""
from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import frontmatter

from hindsight.data.models import Document


def _as_date(value: object, doc_path: Path) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise ValueError(f"{doc_path.name}: 'published_at' missing or invalid: {value!r}")


def load_documents(docs_dir: Path) -> list[Document]:
    docs: list[Document] = []
    for path in sorted(docs_dir.glob("*.md")):
        post = frontmatter.load(path)
        meta = post.metadata
        if "published_at" not in meta:
            raise ValueError(f"{path.name}: frontmatter must include 'published_at'")
        docs.append(
            Document(
                doc_id=path.stem,
                title=str(meta.get("title", path.stem)),
                source=str(meta.get("source", "")),
                published_at=_as_date(meta["published_at"], path),
                url=str(meta.get("url", "")),
                doc_type=str(meta.get("doc_type", "news")),
                text=post.content.strip(),
            )
        )
    return docs
```

Also create empty `backend/hindsight/data/__init__.py` and `backend/hindsight/rag/__init__.py`.

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_ingest.py -q`
Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/data backend/hindsight/rag backend/tests/test_ingest.py
git commit -m "feat(d1): data models and frontmatter document ingest"
```

---

### Task 4: Chunker

Implements spec §4.2: split markdown into ~300–500-token chunks (approximated as ~1600 chars), chunk inherits `published_at`.

**Files:**
- Create: `backend/hindsight/rag/chunker.py`
- Test: `backend/tests/test_chunker.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_chunker.py`:

```python
from datetime import date

from hindsight.data.models import Document
from hindsight.rag.chunker import chunk_document


def make_doc(text: str) -> Document:
    return Document(
        doc_id="d1",
        title="T",
        source="s",
        published_at=date(2025, 3, 1),
        text=text,
    )


def test_short_doc_is_single_chunk():
    chunks = chunk_document(make_doc("one short paragraph"))
    assert len(chunks) == 1
    assert chunks[0].chunk_id == "d1::000"
    assert chunks[0].published_at == date(2025, 3, 1)


def test_long_doc_splits_and_ids_are_sequential():
    para = "word " * 120  # ~600 chars
    text = "\n\n".join(para for _ in range(10))  # ~6000 chars
    chunks = chunk_document(make_doc(text), target_chars=1600)
    assert len(chunks) >= 3
    assert [c.chunk_id for c in chunks] == [f"d1::{i:03d}" for i in range(len(chunks))]
    assert all(len(c.text) <= 2 * 1600 for c in chunks)


def test_headings_start_new_chunks():
    text = "# Section A\n\n" + "a " * 100 + "\n\n# Section B\n\n" + "b " * 100
    chunks = chunk_document(make_doc(text), target_chars=150)
    joined = [c.text for c in chunks]
    assert any(t.startswith("# Section B") for t in joined)


def test_no_empty_chunks():
    chunks = chunk_document(make_doc("a\n\n\n\n\n\nb"))
    assert all(c.text.strip() for c in chunks)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_chunker.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/rag/chunker.py`**

```python
"""Greedy paragraph packer: split on blank lines, start fresh at headings."""
from __future__ import annotations

import re

from hindsight.data.models import Chunk, Document

_HEADING = re.compile(r"^#{1,6}\s")


def chunk_document(doc: Document, target_chars: int = 1600) -> list[Chunk]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", doc.text) if p.strip()]
    buckets: list[str] = []
    current: list[str] = []
    size = 0
    for para in paragraphs:
        is_heading = bool(_HEADING.match(para))
        if current and (is_heading or size + len(para) > target_chars):
            buckets.append("\n\n".join(current))
            current, size = [], 0
        current.append(para)
        size += len(para)
    if current:
        buckets.append("\n\n".join(current))
    return [
        Chunk(
            chunk_id=f"{doc.doc_id}::{i:03d}",
            doc_id=doc.doc_id,
            title=doc.title,
            published_at=doc.published_at,
            text=text,
        )
        for i, text in enumerate(buckets)
    ]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_chunker.py -q`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/rag/chunker.py backend/tests/test_chunker.py
git commit -m "feat(d1): markdown chunker with heading-aware packing"
```

---

### Task 5: Time-filtered BM25 retriever

Implements spec §4.2. Filter-then-index: chunks are filtered to `published_at <= as_of` **before** the BM25 index is built, so even IDF statistics never see future documents (interview-grade purity; document this in the docstring).

**Files:**
- Create: `backend/hindsight/rag/bm25_retriever.py`
- Test: `backend/tests/test_bm25_retriever.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_bm25_retriever.py`:

```python
from datetime import date

from hindsight.data.models import Chunk
from hindsight.rag.bm25_retriever import BM25Retriever


def make_chunk(cid: str, text: str, published: date) -> Chunk:
    return Chunk(
        chunk_id=cid,
        doc_id=cid.split("::")[0],
        title=cid,
        published_at=published,
        text=text,
    )


CORPUS = [
    make_chunk("a::000", "nvidia data center revenue beat expectations", date(2025, 2, 27)),
    make_chunk("b::000", "tesla delivery numbers missed estimates badly", date(2025, 3, 5)),
    make_chunk("c::000", "nvidia blackwell supply chain ramping fast", date(2025, 4, 10)),
    make_chunk("d::000", "macro semis outlook mixed on tariffs", date(2025, 4, 20)),
    make_chunk("future::000", "nvidia earnings results smashed records", date(2025, 5, 28)),
]


def test_relevant_chunk_ranks_first():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia data center revenue", as_of=date(2025, 5, 22), top_k=3)
    assert results[0].chunk.chunk_id == "a::000"
    assert results[0].score > 0


def test_future_chunks_never_returned():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia earnings results", as_of=date(2025, 5, 22), top_k=5)
    ids = [s.chunk.chunk_id for s in results]
    assert "future::000" not in ids


def test_as_of_boundary_is_inclusive():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia earnings results", as_of=date(2025, 5, 28), top_k=5)
    ids = [s.chunk.chunk_id for s in results]
    assert "future::000" in ids


def test_empty_when_nothing_visible():
    r = BM25Retriever(CORPUS)
    assert r.search("anything", as_of=date(2024, 1, 1), top_k=3) == []


def test_top_k_respected():
    r = BM25Retriever(CORPUS)
    results = r.search("nvidia", as_of=date(2025, 5, 22), top_k=2)
    assert len(results) <= 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_bm25_retriever.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/rag/bm25_retriever.py`**

```python
"""Time-filtered BM25 retrieval.

Filter-then-index: visible chunks are selected by published_at <= as_of
BEFORE the BM25 index is built, so corpus statistics (IDF) never observe
future documents. Rebuilding per query is fine at our corpus sizes
(hundreds of chunks).

Note: BM25Okapi IDF can zero out terms present in ~half the corpus when
the corpus is tiny (2-3 chunks). Case datasets enforce a minimum corpus
size instead of patching the scorer.
"""
from __future__ import annotations

import re
from datetime import date

from rank_bm25 import BM25Okapi

from hindsight.data.models import Chunk, ScoredChunk

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class BM25Retriever:
    def __init__(self, chunks: list[Chunk]):
        self._chunks = list(chunks)

    def search(self, query: str, as_of: date, top_k: int = 5) -> list[ScoredChunk]:
        visible = [c for c in self._chunks if c.published_at <= as_of]
        if not visible:
            return []
        index = BM25Okapi([_tokenize(c.text) for c in visible])
        scores = index.get_scores(_tokenize(query))
        ranked = sorted(zip(visible, scores), key=lambda p: p[1], reverse=True)
        return [
            ScoredChunk(chunk=c, score=float(s)) for c, s in ranked[:top_k] if s > 0
        ] or [ScoredChunk(chunk=c, score=float(s)) for c, s in ranked[: min(top_k, 1)]]
```

The trailing `or [...]` keeps dry-run demos useful on tiny fixture corpora (all-zero scores return the single best candidate rather than nothing); with a real case corpus scores are positive and it never triggers.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_bm25_retriever.py -q`
Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add backend/hindsight/rag/bm25_retriever.py backend/tests/test_bm25_retriever.py
git commit -m "feat(d1): time-filtered BM25 retriever (filter-then-index)"
```

---

### Task 6: Market data sources + freeze script

Implements spec §4.1: `MarketDataSource` protocol, `FrozenBarsSource` (reads committed `bars.json` snapshots — the runtime path), `YFinanceSource` (case-authoring path, `auto_adjust=True` explicit), and `scripts/freeze_case_bars.py`. Tests use fixtures only — **no network in tests**.

**Files:**
- Create: `backend/hindsight/data/market_source.py`
- Create: `backend/scripts/freeze_case_bars.py`
- Test: `backend/tests/test_market_source.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_market_source.py`:

```python
import json
from datetime import date

import pytest

from hindsight.data.market_source import FrozenBarsSource

BARS = {
    "ticker": "NVDA",
    "auto_adjust": True,
    "fetched_at": "2026-07-04T12:00:00",
    "bars": [
        {"date": "2025-05-20", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
        {"date": "2025-05-21", "open": 1.5, "high": 2.5, "low": 1, "close": 2.0, "volume": 110},
        {"date": "2025-05-22", "open": 2.0, "high": 3.0, "low": 1.5, "close": 2.5, "volume": 120},
    ],
}


@pytest.fixture
def source(tmp_path):
    p = tmp_path / "bars.json"
    p.write_text(json.dumps(BARS), encoding="utf-8")
    return FrozenBarsSource(p)


def test_range_filter_inclusive(source):
    bars = source.get_bars("NVDA", date(2025, 5, 21), date(2025, 5, 22))
    assert [b.date.isoformat() for b in bars] == ["2025-05-21", "2025-05-22"]
    assert bars[0].close == 2.0


def test_unknown_ticker_raises(source):
    with pytest.raises(ValueError, match="TSLA"):
        source.get_bars("TSLA", date(2025, 5, 20), date(2025, 5, 22))


def test_bars_sorted_by_date(source):
    bars = source.get_bars("NVDA", date(2025, 1, 1), date(2026, 1, 1))
    assert [b.date for b in bars] == sorted(b.date for b in bars)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_market_source.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/data/market_source.py`**

```python
"""Market data sources. Runtime always reads frozen snapshots (spec §4.1)."""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Protocol

from hindsight.data.models import Bar


class MarketDataSource(Protocol):
    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        """Daily adjusted OHLCV bars with start <= bar.date <= end."""
        ...


class FrozenBarsSource:
    """Reads a bars.json snapshot committed under datasets/<case_id>/."""

    def __init__(self, bars_path: Path):
        payload = json.loads(Path(bars_path).read_text(encoding="utf-8"))
        self._ticker: str = payload["ticker"]
        self._bars = sorted(
            (Bar(**b) for b in payload["bars"]), key=lambda b: b.date
        )

    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        if ticker != self._ticker:
            raise ValueError(f"snapshot holds {self._ticker}, not {ticker}")
        return [b for b in self._bars if start <= b.date <= end]


class YFinanceSource:
    """Case-authoring source. Not used at runtime; import stays lazy."""

    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        import yfinance as yf

        df = yf.download(
            ticker,
            start=start.isoformat(),
            end=(end + timedelta(days=1)).isoformat(),  # yf.download end is exclusive; protocol is inclusive
            progress=False,
            auto_adjust=True,  # explicit: adjusted prices, never rely on defaults
        )
        if df is None or df.empty:
            raise ValueError(f"yfinance returned no data for {ticker}")
        if hasattr(df.columns, "levels"):  # flatten MultiIndex columns
            df.columns = [c[0] for c in df.columns]
        return [
            Bar(
                date=idx.date(),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=float(row["Volume"]),
            )
            for idx, row in df.iterrows()
        ]
```

- [ ] **Step 4: Write `backend/scripts/freeze_case_bars.py`**

```python
"""Fetch adjusted bars for a case and freeze them to datasets/<case_id>/bars.json.

Usage (from repo root):
    backend/.venv/Scripts/python backend/scripts/freeze_case_bars.py \
        --case datasets/nvda_fy26q1 --start 2025-01-02 --end 2025-08-15

The snapshot is committed to git and never refreshed automatically —
baseline and outcome prices must come from the same fetch (spec §4.1).
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path

from hindsight.data.market_source import YFinanceSource


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", required=True, help="path to datasets/<case_id>")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    args = ap.parse_args()

    case_dir = Path(args.case)
    meta = json.loads((case_dir / "meta.json").read_text(encoding="utf-8"))
    ticker = meta["ticker"]

    import yfinance as yf

    bars = YFinanceSource().get_bars(
        ticker, date.fromisoformat(args.start), date.fromisoformat(args.end)
    )
    payload = {
        "ticker": ticker,
        "auto_adjust": True,
        "yfinance_version": yf.__version__,
        "fetched_at": datetime.now().isoformat(timespec="seconds"),
        "bars": [
            {
                "date": b.date.isoformat(),
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
            }
            for b in bars
        ],
    }
    out = case_dir / "bars.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"froze {len(bars)} bars for {ticker} -> {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_market_source.py -q`
Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/data/market_source.py backend/scripts/freeze_case_bars.py backend/tests/test_market_source.py
git commit -m "feat(d1): frozen/yfinance market sources and freeze script"
```

---

### Task 7: Time sandbox — errors, audit log, gates + leakage tests

The crown jewel (spec §3.2). Two wrappers gate every data access; both write audit entries. Corpus access filters silently (retrieval semantics); market access **raises** `LookaheadError` when the requested range extends past `as_of`.

**Files:**
- Create: `backend/hindsight/sandbox/__init__.py` (empty)
- Create: `backend/hindsight/sandbox/errors.py`
- Create: `backend/hindsight/sandbox/audit.py`
- Create: `backend/hindsight/sandbox/gate.py`
- Test: `backend/tests/test_sandbox_leakage.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_sandbox_leakage.py`:

```python
"""Leakage tests: no code path may return information dated after as_of.

Channels covered here: documents, market bars. The experience-card channel
is added in D2 alongside the experience library (spec §9).
"""
import json
from datetime import date

import pytest

from hindsight.data.market_source import FrozenBarsSource
from hindsight.data.models import Chunk
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.errors import LookaheadError
from hindsight.sandbox.gate import SandboxedCorpus, SandboxedMarketData

AS_OF = date(2025, 5, 22)


def make_chunk(cid: str, text: str, published: date) -> Chunk:
    return Chunk(chunk_id=cid, doc_id=cid, title=cid, published_at=published, text=text)


@pytest.fixture
def corpus():
    chunks = [
        make_chunk("past", "nvidia guidance strong before earnings", date(2025, 5, 1)),
        make_chunk("future", "nvidia earnings smashed records after report", date(2025, 5, 28)),
    ]
    return SandboxedCorpus(BM25Retriever(chunks), as_of=AS_OF, audit=AuditLog())


@pytest.fixture
def market(tmp_path):
    payload = {
        "ticker": "NVDA",
        "auto_adjust": True,
        "fetched_at": "x",
        "bars": [
            {"date": "2025-05-21", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1},
            {"date": "2025-05-22", "open": 1, "high": 1, "low": 1, "close": 2, "volume": 1},
            {"date": "2025-05-23", "open": 1, "high": 1, "low": 1, "close": 9, "volume": 1},
        ],
    }
    p = tmp_path / "bars.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    return SandboxedMarketData(FrozenBarsSource(p), as_of=AS_OF, audit=AuditLog())


def test_corpus_never_returns_future_docs(corpus):
    results = corpus.search("nvidia earnings records report", top_k=5)
    assert results, "past doc should still be retrievable"
    assert all(s.chunk.published_at <= AS_OF for s in results)
    assert all(s.chunk.chunk_id != "future" for s in results)


def test_corpus_writes_audit_entry(corpus):
    corpus.search("nvidia", top_k=2)
    entries = corpus.audit.entries
    assert entries and entries[-1].tool == "corpus_search"
    assert entries[-1].data_max_date is not None
    assert entries[-1].data_max_date <= AS_OF


def test_market_range_ending_after_as_of_raises(market):
    with pytest.raises(LookaheadError):
        market.get_bars("NVDA", date(2025, 5, 21), date(2025, 5, 23))


def test_market_range_up_to_as_of_allowed(market):
    bars = market.get_bars("NVDA", date(2025, 5, 21), AS_OF)
    assert [b.date.isoformat() for b in bars] == ["2025-05-21", "2025-05-22"]
    assert all(b.date <= AS_OF for b in bars)


def test_market_writes_audit_entry(market):
    market.get_bars("NVDA", date(2025, 5, 21), AS_OF)
    entry = market.audit.entries[-1]
    assert entry.tool == "market_data"
    assert entry.data_max_date == AS_OF


def test_denied_market_access_is_audited(market):
    with pytest.raises(LookaheadError):
        market.get_bars("NVDA", date(2025, 5, 21), date(2025, 6, 30))
    entry = market.audit.entries[-1]
    assert entry.note == "DENIED lookahead"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_sandbox_leakage.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/sandbox/errors.py`**

```python
class LookaheadError(Exception):
    """A tool requested data dated after the run's as_of date."""
```

- [ ] **Step 4: Write `backend/hindsight/sandbox/audit.py`**

```python
"""Audit log: every sandboxed data access leaves a row (spec §3.2)."""
from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    tool: str
    params: dict[str, Any] = Field(default_factory=dict)
    data_max_date: date | None = None
    note: str = ""


class AuditLog:
    def __init__(self) -> None:
        self.entries: list[AuditEntry] = []

    def record(
        self,
        tool: str,
        params: dict[str, Any],
        data_max_date: date | None = None,
        note: str = "",
    ) -> None:
        self.entries.append(
            AuditEntry(tool=tool, params=params, data_max_date=data_max_date, note=note)
        )

    def as_dicts(self) -> list[dict[str, Any]]:
        return [e.model_dump(mode="json") for e in self.entries]
```

- [ ] **Step 5: Write `backend/hindsight/sandbox/gate.py`**

```python
"""as_of information gates. All agent-facing data access goes through here."""
from __future__ import annotations

from datetime import date

from hindsight.data.market_source import MarketDataSource
from hindsight.data.models import Bar, ScoredChunk
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.errors import LookaheadError


class SandboxedCorpus:
    def __init__(self, retriever: BM25Retriever, as_of: date, audit: AuditLog):
        self._retriever = retriever
        self.as_of = as_of
        self.audit = audit

    def search(self, query: str, top_k: int = 5) -> list[ScoredChunk]:
        results = self._retriever.search(query, as_of=self.as_of, top_k=top_k)
        self.audit.record(
            tool="corpus_search",
            params={"query": query, "top_k": top_k},
            data_max_date=max((s.chunk.published_at for s in results), default=None),
        )
        return results


class SandboxedMarketData:
    def __init__(self, source: MarketDataSource, as_of: date, audit: AuditLog):
        self._source = source
        self.as_of = as_of
        self.audit = audit

    def get_bars(self, ticker: str, start: date, end: date) -> list[Bar]:
        if end > self.as_of:
            self.audit.record(
                tool="market_data",
                params={"ticker": ticker, "start": str(start), "end": str(end)},
                note="DENIED lookahead",
            )
            raise LookaheadError(
                f"requested bars up to {end}, but as_of is {self.as_of}"
            )
        bars = self._source.get_bars(ticker, start, end)
        self.audit.record(
            tool="market_data",
            params={"ticker": ticker, "start": str(start), "end": str(end)},
            data_max_date=max((b.date for b in bars), default=None),
        )
        return bars
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_sandbox_leakage.py -q`
Expected: `6 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/hindsight/sandbox backend/tests/test_sandbox_leakage.py
git commit -m "feat(d1): time sandbox gates, audit log, leakage tests"
```

---

### Task 8: Tool registry + three tools

Implements spec §3.1 tool allowlists / §2 "统一工具注册表". Tools return JSON strings (what the LLM sees). The registry emits OpenAI `tools` schemas; the same specs serve the prompt-JSON fallback mode.

**Files:**
- Create: `backend/hindsight/tools/__init__.py` (empty)
- Create: `backend/hindsight/tools/registry.py`
- Create: `backend/hindsight/tools/market_data.py`
- Create: `backend/hindsight/tools/corpus_search.py`
- Create: `backend/hindsight/tools/calc.py`
- Test: `backend/tests/test_tools.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_tools.py`:

```python
import json
from datetime import date

import pytest

from hindsight.data.models import Chunk
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.gate import SandboxedCorpus
from hindsight.tools.calc import make_calc_tool
from hindsight.tools.corpus_search import make_corpus_tool
from hindsight.tools.registry import ToolRegistry

AS_OF = date(2025, 5, 22)


@pytest.fixture
def registry():
    chunks = [
        Chunk(
            chunk_id="a::000",
            doc_id="a",
            title="NVDA guidance",
            published_at=date(2025, 5, 1),
            text="nvidia guidance strong data center demand",
        )
    ]
    corpus = SandboxedCorpus(BM25Retriever(chunks), as_of=AS_OF, audit=AuditLog())
    reg = ToolRegistry()
    reg.register(make_corpus_tool(corpus))
    reg.register(make_calc_tool())
    return reg


def test_openai_specs_shape(registry):
    specs = registry.openai_specs()
    names = {s["function"]["name"] for s in specs}
    assert names == {"corpus_search", "calc"}
    assert all(s["type"] == "function" for s in specs)
    assert all("parameters" in s["function"] for s in specs)


def test_dispatch_corpus_search(registry):
    out = registry.call("corpus_search", {"query": "nvidia guidance", "top_k": 3})
    payload = json.loads(out)
    assert payload["results"][0]["chunk_id"] == "a::000"
    assert payload["results"][0]["published_at"] == "2025-05-01"


def test_dispatch_calc(registry):
    out = registry.call("calc", {"expression": "(2.5 - 2.0) / 2.0 * 100"})
    assert json.loads(out)["value"] == pytest.approx(25.0)


def test_calc_rejects_non_arithmetic(registry):
    out = registry.call("calc", {"expression": "__import__('os')"})
    assert "error" in json.loads(out)


def test_unknown_tool_raises(registry):
    with pytest.raises(KeyError):
        registry.call("nope", {})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_tools.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/tools/registry.py`**

```python
"""Tool registry: named tools with JSON-schema params, OpenAI-spec export."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema for the arguments object
    fn: Callable[..., str]  # returns a JSON string shown to the LLM


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def openai_specs(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in self._tools.values()
        ]

    def call(self, name: str, args: dict[str, Any]) -> str:
        return self._tools[name].fn(**args)
```

- [ ] **Step 4: Write `backend/hindsight/tools/corpus_search.py`**

```python
"""corpus_search tool: time-filtered retrieval over the case corpus."""
from __future__ import annotations

import json

from hindsight.sandbox.gate import SandboxedCorpus
from hindsight.tools.registry import ToolSpec

_EXCERPT_CHARS = 700


def make_corpus_tool(corpus: SandboxedCorpus) -> ToolSpec:
    def corpus_search(query: str, top_k: int = 5) -> str:
        results = corpus.search(query, top_k=top_k)
        return json.dumps(
            {
                "results": [
                    {
                        "chunk_id": s.chunk.chunk_id,
                        "title": s.chunk.title,
                        "published_at": s.chunk.published_at.isoformat(),
                        "score": round(s.score, 3),
                        "excerpt": s.chunk.text[:_EXCERPT_CHARS],
                    }
                    for s in results
                ]
            }
        )

    return ToolSpec(
        name="corpus_search",
        description=(
            "Search the research corpus (news, filings, transcripts). "
            "Only documents published on or before the as_of date are visible."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "keyword query"},
                "top_k": {"type": "integer", "default": 5, "minimum": 1},
            },
            "required": ["query"],
        },
        fn=corpus_search,
    )
```

- [ ] **Step 5: Write `backend/hindsight/tools/market_data.py`**

```python
"""market_data tool: adjusted price history up to as_of, with derived stats."""
from __future__ import annotations

import json
from datetime import date, timedelta

from hindsight.sandbox.errors import LookaheadError
from hindsight.sandbox.gate import SandboxedMarketData
from hindsight.tools.registry import ToolSpec


def make_market_tool(market: SandboxedMarketData, ticker: str) -> ToolSpec:
    def price_history(lookback_days: int = 60) -> str:
        end = market.as_of
        start = end - timedelta(days=lookback_days)
        try:
            bars = market.get_bars(ticker, start, end)
        except LookaheadError as exc:  # defensive; end==as_of never triggers it
            return json.dumps({"error": str(exc)})
        if not bars:
            return json.dumps({"error": f"no bars for {ticker} in window"})
        closes = [b.close for b in bars]
        pct = (closes[-1] / closes[0] - 1) * 100 if closes[0] else 0.0
        return json.dumps(
            {
                "ticker": ticker,
                "as_of": end.isoformat(),
                "bars": [
                    {"date": b.date.isoformat(), "close": round(b.close, 4)}
                    for b in bars
                ],
                "window_return_pct": round(pct, 2),
                "last_close": round(closes[-1], 4),
            }
        )

    return ToolSpec(
        name="price_history",
        description=(
            f"Daily adjusted closes for {ticker} ending at the as_of date. "
            "Data after as_of does not exist for this run."
        ),
        parameters={
            "type": "object",
            "properties": {
                "lookback_days": {"type": "integer", "default": 60},
            },
            "required": [],
        },
        fn=price_history,
    )
```

- [ ] **Step 6: Write `backend/hindsight/tools/calc.py`**

```python
"""calc tool: safe arithmetic via AST allowlist (no eval of names/calls)."""
from __future__ import annotations

import ast
import json
import operator

from hindsight.tools.registry import ToolSpec

_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        return _BIN[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY:
        return _UNARY[type(node.op)](_eval(node.operand))
    raise ValueError(f"unsupported expression element: {ast.dump(node)[:60]}")


def make_calc_tool() -> ToolSpec:
    def calc(expression: str) -> str:
        try:
            value = _eval(ast.parse(expression, mode="eval"))
            return json.dumps({"value": value})
        except (ValueError, SyntaxError, ZeroDivisionError) as exc:
            return json.dumps({"error": str(exc)})

    return ToolSpec(
        name="calc",
        description="Evaluate a plain arithmetic expression (numbers and + - * / ** % only).",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        },
        fn=calc,
    )
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_tools.py -q`
Expected: `5 passed`

- [ ] **Step 8: Commit**

```bash
git add backend/hindsight/tools backend/tests/test_tools.py
git commit -m "feat(d1): tool registry with corpus/market/calc tools"
```

---

### Task 9: Trace recorder + cost ledger

Implements spec §4.3 run 落盘 / §5 event protocol. Events go to `runs/<run_id>/trace.jsonl` and stay in memory for tests/UI.

**Files:**
- Create: `backend/hindsight/trace/__init__.py` (empty)
- Create: `backend/hindsight/trace/events.py`
- Create: `backend/hindsight/trace/recorder.py`
- Create: `backend/hindsight/trace/cost_ledger.py`
- Test: `backend/tests/test_trace.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_trace.py`:

```python
import json

from hindsight.trace.cost_ledger import CostLedger
from hindsight.trace.events import TraceEvent
from hindsight.trace.recorder import TraceRecorder


def test_recorder_appends_jsonl_and_memory(tmp_path):
    rec = TraceRecorder(run_dir=tmp_path)
    rec.emit(TraceEvent(type="tool_call", agent="planner", payload={"tool": "calc"}))
    rec.emit(TraceEvent(type="tool_result", agent="planner", payload={"ok": True}, tokens=12))
    lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["type"] == "tool_call"
    assert first["agent"] == "planner"
    assert "ts" in first
    assert len(rec.events) == 2


def test_event_type_is_validated():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        TraceEvent(type="not_a_type", agent="x", payload={})


def test_cost_ledger_accumulates_per_agent():
    ledger = CostLedger()
    ledger.add("planner", prompt_tokens=100, completion_tokens=20)
    ledger.add("planner", prompt_tokens=50, completion_tokens=10)
    ledger.add("analyst", prompt_tokens=200, completion_tokens=80)
    s = ledger.summary()
    assert s["planner"] == {"prompt_tokens": 150, "completion_tokens": 30, "calls": 2}
    assert s["analyst"]["calls"] == 1
    assert ledger.total_tokens() == 460
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_trace.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/trace/events.py`**

```python
"""Structured trace events. Protocol shared by live stream and replay (spec §5)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

EventType = Literal[
    "plan_step",
    "tool_call",
    "tool_result",
    "agent_output",
    "validation",
    "context_trim",
    "score",
    "audit",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class TraceEvent(BaseModel):
    type: EventType
    agent: str
    payload: dict[str, Any] = Field(default_factory=dict)
    tokens: int = 0
    ts: str = Field(default_factory=_now_iso)
```

- [ ] **Step 4: Write `backend/hindsight/trace/recorder.py`**

```python
"""Flight recorder: append-only jsonl + in-memory list."""
from __future__ import annotations

from pathlib import Path

from hindsight.trace.events import TraceEvent


class TraceRecorder:
    def __init__(self, run_dir: Path):
        self.run_dir = Path(run_dir)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self._path = self.run_dir / "trace.jsonl"
        self.events: list[TraceEvent] = []

    def emit(self, event: TraceEvent) -> None:
        self.events.append(event)
        with self._path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
```

- [ ] **Step 5: Write `backend/hindsight/trace/cost_ledger.py`**

```python
"""Per-agent token accounting (spec §3.4 track C)."""
from __future__ import annotations

from collections import defaultdict


class CostLedger:
    def __init__(self) -> None:
        self._by_agent: dict[str, dict[str, int]] = defaultdict(
            lambda: {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0}
        )

    def add(self, agent: str, prompt_tokens: int, completion_tokens: int) -> None:
        row = self._by_agent[agent]
        row["prompt_tokens"] += prompt_tokens
        row["completion_tokens"] += completion_tokens
        row["calls"] += 1

    def summary(self) -> dict[str, dict[str, int]]:
        return {agent: dict(row) for agent, row in self._by_agent.items()}

    def total_tokens(self) -> int:
        return sum(
            row["prompt_tokens"] + row["completion_tokens"]
            for row in self._by_agent.values()
        )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_trace.py -q`
Expected: `3 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/hindsight/trace backend/tests/test_trace.py
git commit -m "feat(d1): trace recorder and cost ledger"
```

---

### Task 10: LLM client + record/replay layer

Implements spec §4.4. The client is transport-injected: production transport wraps the `openai` SDK; tests inject a fake transport — **no network in tests**. Replay keys on a SHA-256 of the canonical request JSON. `HINDSIGHT_OFFLINE=1` (or `offline=True`) means a cache miss raises `ReplayMissError` instead of calling out.

**Files:**
- Create: `backend/hindsight/llm/__init__.py` (empty)
- Create: `backend/hindsight/llm/client.py`
- Create: `backend/hindsight/llm/recording.py`
- Test: `backend/tests/test_replay.py`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_replay.py`:

```python
import pytest

from hindsight.llm.recording import RecordingLLMClient, ReplayMissError


def fake_response(text: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": text}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }


def test_records_then_replays_without_transport(tmp_path):
    calls = []

    def transport(request: dict) -> dict:
        calls.append(request)
        return fake_response("hello")

    db = tmp_path / "llm_calls.sqlite"
    c1 = RecordingLLMClient(transport=transport, db_path=db, model="m1")
    r1 = c1.chat(messages=[{"role": "user", "content": "hi"}])
    assert r1["choices"][0]["message"]["content"] == "hello"
    assert len(calls) == 1

    # same request again: served from cache, transport NOT called
    r2 = c1.chat(messages=[{"role": "user", "content": "hi"}])
    assert r2 == r1
    assert len(calls) == 1

    # new client on same db, offline: still served
    def exploding_transport(request: dict) -> dict:
        raise AssertionError("offline client must not call transport")

    c2 = RecordingLLMClient(
        transport=exploding_transport, db_path=db, model="m1", offline=True
    )
    r3 = c2.chat(messages=[{"role": "user", "content": "hi"}])
    assert r3["choices"][0]["message"]["content"] == "hello"


def test_offline_miss_raises_with_hash(tmp_path):
    c = RecordingLLMClient(
        transport=lambda req: fake_response("x"),
        db_path=tmp_path / "db.sqlite",
        model="m1",
        offline=True,
    )
    with pytest.raises(ReplayMissError) as exc:
        c.chat(messages=[{"role": "user", "content": "never seen"}])
    assert len(str(exc.value)) > 20  # message carries the request hash


def test_key_varies_with_params(tmp_path):
    responses = iter([fake_response("a"), fake_response("b")])
    c = RecordingLLMClient(
        transport=lambda req: next(responses),
        db_path=tmp_path / "db.sqlite",
        model="m1",
    )
    r1 = c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0.0)
    r2 = c.chat(messages=[{"role": "user", "content": "hi"}], temperature=0.9)
    assert r1["choices"][0]["message"]["content"] == "a"
    assert r2["choices"][0]["message"]["content"] == "b"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_replay.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write `backend/hindsight/llm/client.py`**

```python
"""LLM config from .env and the production transport (openai SDK)."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv
from pydantic import BaseModel

Transport = Callable[[dict[str, Any]], dict[str, Any]]


class LLMConfig(BaseModel):
    base_url: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls, dotenv_path: Path | None = None) -> "LLMConfig":
        load_dotenv(dotenv_path)  # repo-root .env by default
        return cls(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ["LLM_API_KEY"],
            model=os.environ["LLM_MODEL"],
        )


def openai_transport(config: LLMConfig) -> Transport:
    from openai import OpenAI

    client = OpenAI(base_url=config.base_url, api_key=config.api_key)

    def send(request: dict[str, Any]) -> dict[str, Any]:
        response = client.chat.completions.create(**request)
        return response.model_dump()

    return send
```

- [ ] **Step 4: Write `backend/hindsight/llm/recording.py`**

```python
"""Record/replay layer over any transport (spec §4.4).

Every request is canonicalized (sorted-keys JSON) and hashed; responses are
stored in SQLite. Cache hit -> no network. offline=True -> cache miss raises
ReplayMissError instead of calling the transport.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hindsight.llm.client import Transport


class ReplayMissError(Exception):
    """Offline mode requested a call that was never recorded."""


class RecordingLLMClient:
    def __init__(
        self,
        transport: Transport,
        db_path: Path,
        model: str,
        offline: bool | None = None,
    ):
        self._transport = transport
        self.model = model
        if offline is None:
            offline = os.environ.get("HINDSIGHT_OFFLINE", "") == "1"
        self.offline = offline
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS llm_calls ("
            " hash TEXT PRIMARY KEY, request_json TEXT NOT NULL,"
            " response_json TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self._conn.commit()

    @staticmethod
    def _key(request: dict[str, Any]) -> str:
        canonical = json.dumps(request, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.2,
        **params: Any,
    ) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            **params,
        }
        if tools is not None:
            request["tools"] = tools
        key = self._key(request)
        row = self._conn.execute(
            "SELECT response_json FROM llm_calls WHERE hash = ?", (key,)
        ).fetchone()
        if row:
            return json.loads(row[0])
        if self.offline:
            raise ReplayMissError(
                f"offline replay miss for request hash {key}; "
                "re-run in record mode to capture it"
            )
        response = self._transport(request)
        self._conn.execute(
            "INSERT OR REPLACE INTO llm_calls VALUES (?, ?, ?, ?)",
            (
                key,
                json.dumps(request, ensure_ascii=False),
                json.dumps(response, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
            ),
        )
        self._conn.commit()
        return response
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_replay.py -q`
Expected: `3 passed`

- [ ] **Step 6: Commit**

```bash
git add backend/hindsight/llm backend/tests/test_replay.py
git commit -m "feat(d1): transport-injected LLM client with sqlite record/replay"
```

---

### Task 11: Case loader + CLI dry-run

Wires everything together without any LLM: load a case directory, build sandboxed corpus + market, run a query, print results and the audit log, and show a blocked lookahead attempt.

**Files:**
- Create: `backend/hindsight/data/cases.py`
- Create: `backend/hindsight/cli.py`
- Test: `backend/tests/test_cases.py`
- Test fixture builder in: `backend/tests/conftest.py`

- [ ] **Step 1: Write `backend/tests/conftest.py` (shared case fixture)**

```python
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
```

- [ ] **Step 2: Write the failing tests**

`backend/tests/test_cases.py`:

```python
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
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_cases.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write `backend/hindsight/data/cases.py`**

```python
"""Case loading: datasets/<case_id>/ -> meta + documents + chunks + bars."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from hindsight.data.market_source import FrozenBarsSource
from hindsight.data.models import CaseMeta, Chunk, Document
from hindsight.rag.chunker import chunk_document
from hindsight.rag.ingest import load_documents

MIN_CORPUS_DOCS = 2  # BM25 degenerates below this; real cases carry 10+


@dataclass
class Case:
    meta: CaseMeta
    documents: list[Document]
    chunks: list[Chunk]
    bars_source: FrozenBarsSource


def load_case(case_dir: Path) -> Case:
    case_dir = Path(case_dir)
    meta = CaseMeta(**json.loads((case_dir / "meta.json").read_text(encoding="utf-8")))
    documents = load_documents(case_dir / "docs")
    if len(documents) < MIN_CORPUS_DOCS:
        raise ValueError(
            f"case {meta.case_id}: needs >= {MIN_CORPUS_DOCS} docs, got {len(documents)}"
        )
    chunks = [c for d in documents for c in chunk_document(d)]
    return Case(
        meta=meta,
        documents=documents,
        chunks=chunks,
        bars_source=FrozenBarsSource(case_dir / "bars.json"),
    )
```

- [ ] **Step 5: Write `backend/hindsight/cli.py`**

```python
"""CLI dry-run: exercise sandbox + retrieval + market data with no LLM.

Usage (from repo root):
    backend/.venv/Scripts/python -m hindsight.cli dry-run \
        --case datasets/nvda_fy26q1 --query "data center demand"
"""
from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

from hindsight.data.cases import load_case
from hindsight.rag.bm25_retriever import BM25Retriever
from hindsight.sandbox.audit import AuditLog
from hindsight.sandbox.errors import LookaheadError
from hindsight.sandbox.gate import SandboxedCorpus, SandboxedMarketData


def dry_run(case_dir: Path, query: str) -> None:
    case = load_case(case_dir)
    as_of = case.meta.as_of
    audit = AuditLog()
    corpus = SandboxedCorpus(BM25Retriever(case.chunks), as_of=as_of, audit=audit)
    market = SandboxedMarketData(case.bars_source, as_of=as_of, audit=audit)

    print(f"== case {case.meta.case_id} | ticker {case.meta.ticker} | as_of {as_of} ==")
    print(f"\n-- corpus_search: {query!r}")
    for s in corpus.search(query, top_k=5):
        print(f"  [{s.score:6.2f}] {s.chunk.chunk_id}  ({s.chunk.published_at})  {s.chunk.title}")

    print("\n-- price_history (30 calendar days up to as_of)")
    bars = market.get_bars(case.meta.ticker, as_of - timedelta(days=30), as_of)
    if bars:
        pct = (bars[-1].close / bars[0].close - 1) * 100
        print(f"  {len(bars)} bars, window return {pct:+.2f}%, last close {bars[-1].close:.2f}")

    print("\n-- attempting lookahead (should be DENIED)")
    try:
        market.get_bars(case.meta.ticker, as_of, as_of + timedelta(days=30))
    except LookaheadError as exc:
        print(f"  blocked: {exc}")

    print("\n-- audit log")
    for e in audit.as_dicts():
        print(f"  {json.dumps(e, ensure_ascii=False)}")


def main() -> None:
    ap = argparse.ArgumentParser(prog="hindsight")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("dry-run", help="sandboxed retrieval + market data, no LLM")
    p.add_argument("--case", required=True, help="path to datasets/<case_id>")
    p.add_argument("--query", default="latest guidance and demand outlook")
    args = ap.parse_args()
    if args.command == "dry-run":
        dry_run(Path(args.case), args.query)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_cases.py -q`
Expected: `2 passed`

- [ ] **Step 7: Commit**

```bash
git add backend/hindsight/data/cases.py backend/hindsight/cli.py backend/tests/conftest.py backend/tests/test_cases.py
git commit -m "feat(d1): case loader and CLI dry-run"
```

---

### Task 12: Endpoint probe script + eval log

Implements spec §4.4 D1 probe. This is a **manual, network-using script** (not a pytest test): it decides whether D2's Planner uses native function calling or prompt-JSON actions. Results are recorded in `docs/eval-log.md`.

**Files:**
- Create: `backend/scripts/probe_endpoint.py`
- Create: `docs/eval-log.md`

- [ ] **Step 1: Write `backend/scripts/probe_endpoint.py`**

```python
"""Probe the OpenAI-compatible endpoint: native tools support + JSON stability.

Usage (from repo root, consumes 6-7 metered calls):
    backend/.venv/Scripts/python backend/scripts/probe_endpoint.py
"""
from __future__ import annotations

import json

from hindsight.llm.client import LLMConfig, openai_transport

TOOL = {
    "type": "function",
    "function": {
        "name": "get_price",
        "description": "Get the latest price for a ticker",
        "parameters": {
            "type": "object",
            "properties": {"ticker": {"type": "string"}},
            "required": ["ticker"],
        },
    },
}

JSON_PROMPT = (
    "Return ONLY a JSON object (no markdown fence, no prose) with keys: "
    '"action" (string, one of "search"|"finish"), "query" (string), '
    '"confidence" (number 0..1). Topic: NVDA earnings preview.'
)


def probe_native_tools(send) -> bool:
    try:
        resp = send(
            {
                "model": LLMConfig.from_env().model,
                "messages": [{"role": "user", "content": "What is the price of NVDA? Use the tool."}],
                "tools": [TOOL],
                "temperature": 0.0,
            }
        )
        calls = resp["choices"][0]["message"].get("tool_calls")
        if not calls:
            print("native tools: NO tool_calls in response")
            return False
        args = json.loads(calls[0]["function"]["arguments"])
        ok = calls[0]["function"]["name"] == "get_price" and "ticker" in args
        print(f"native tools: tool_calls present, well-formed={ok}: {calls[0]}")
        return ok
    except Exception as exc:  # noqa: BLE001 - probe reports everything
        print(f"native tools: FAILED ({type(exc).__name__}: {exc})")
        return False


def probe_json_stability(send, n: int = 5) -> int:
    cfg = LLMConfig.from_env()
    valid = 0
    for i in range(n):
        resp = send(
            {
                "model": cfg.model,
                "messages": [{"role": "user", "content": JSON_PROMPT + f" (attempt {i})"}],
                "temperature": 0.2,
            }
        )
        text = resp["choices"][0]["message"]["content"].strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            obj = json.loads(text)
            assert obj["action"] in ("search", "finish")
            assert isinstance(obj["confidence"], (int, float))
            valid += 1
            print(f"json attempt {i}: valid")
        except Exception as exc:  # noqa: BLE001
            print(f"json attempt {i}: INVALID ({exc}) raw={text[:120]!r}")
    return valid


def main() -> None:
    cfg = LLMConfig.from_env()
    send = openai_transport(cfg)
    print(f"probing {cfg.base_url} model={cfg.model}\n")
    tools_ok = probe_native_tools(send)
    valid = probe_json_stability(send)
    print(f"\nRESULT: native_tools={tools_ok}, json_valid={valid}/5")
    decision = "native function calling" if tools_ok else "prompt-JSON action format"
    print(f"DECISION for D2 planner: {decision}")
    print("Record this in docs/eval-log.md.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Create `docs/eval-log.md`**

```markdown
# Eval log

Development-time record of evaluation-driven changes: every prompt or
architecture change is logged with before/after suite scores. This file is
the receipts for "evaluation as the primary mechanism to guide behavior".

## D1 — endpoint probe (2026-07-xx)

- Endpoint: xf-yun MaaS, model `astron-code-latest` (GLM-5.2)
- Native `tools/tool_choice` support: _record probe output here_
- JSON stability (5 attempts): _n/5 valid_
- **Decision:** Planner uses _native function calling / prompt-JSON actions_
```

- [ ] **Step 3: Run the probe (manual, uses ~7 metered calls)**

Run: `backend/.venv/Scripts/python backend/scripts/probe_endpoint.py`
Expected: prints per-attempt results and a `DECISION for D2 planner:` line. Fill the probe results into `docs/eval-log.md` (replace the placeholders).

- [ ] **Step 4: Commit**

```bash
git add backend/scripts/probe_endpoint.py docs/eval-log.md
git commit -m "feat(d1): endpoint probe for tool-calling mode decision"
```

---

### Task 13: NVDA case dataset (meta + frozen bars + rough corpus)

Implements spec §4.1 case 1 / §10 D1. ~10 rough curated docs — enough for tests and the D2 e2e; polish happens D4. **Includes one future-dated doc on purpose** (the sandbox must hide it — it doubles as demo material).

**Files:**
- Create: `datasets/nvda_fy26q1/meta.json`
- Create: `datasets/nvda_fy26q1/docs/*.md` (10 files)
- Create: `datasets/nvda_fy26q1/bars.json` (via freeze script, network)
- Test: `backend/tests/test_nvda_case.py`

- [ ] **Step 1: Write `datasets/nvda_fy26q1/meta.json`**

```json
{
  "case_id": "nvda_fy26q1",
  "title": "NVDA into FY2026-Q1 earnings (May 2025)",
  "ticker": "NVDA",
  "as_of": "2025-05-22",
  "outcome_window_days": 40,
  "description": "Research NVDA days before the May 28, 2025 FY26Q1 report: AI capex narrative running hot, H20 China export-control overhang, Blackwell ramp underway.",
  "tags": ["earnings", "semis", "ai-capex"]
}
```

- [ ] **Step 2: Author the corpus docs**

Create 10 markdown files under `datasets/nvda_fy26q1/docs/`. Frontmatter format is fixed (see example); the body is a 150-400 word curated summary written from public knowledge of the period, with the source URL in frontmatter. All summaries state facts as known **at publication date**.

Required set (filename — title — published_at — doc_type):

1. `q4_fy25_recap.md` — NVDA Q4 FY2025 results recap — 2025-02-27 — news
2. `10k_mdna_excerpt.md` — NVIDIA FY2025 10-K MD&A excerpt — 2025-02-26 — filing （这是 8k+ token 长文档载体：从 SEC 公开 10-K 摘录 MD&A 完整章节，多段落，将被切成多个 chunk）
3. `blackwell_ramp.md` — Blackwell ramp supply-chain readout — 2025-03-18 — news
4. `h20_export_restriction.md` — H20 China export restriction and writedown — 2025-04-16 — news
5. `hyperscaler_capex.md` — Hyperscaler capex commentary (MSFT/GOOG/META calls) — 2025-05-02 — news
6. `analyst_preview.md` — Street preview of FY26Q1 — 2025-05-19 — research
7. `amd_competition.md` — AMD MI325X competitive positioning — 2025-04-08 — news
8. `ai_capex_skeptic.md` — The bear case: AI capex digestion risk — 2025-05-10 — opinion
9. `semis_macro.md` — Semis macro: tariffs and export controls backdrop — 2025-04-25 — news
10. `earnings_results_future.md` — NVDA FY26Q1 results (published AFTER as_of) — 2025-05-28 — news （故意的未来文档，验证沙箱 + 演示用）

Example (`q4_fy25_recap.md`) — write the other nine in the same shape:

```markdown
---
title: NVDA Q4 FY2025 results recap
source: curated summary of public reporting
published_at: 2025-02-27
url: https://nvidianews.nvidia.com/news/nvidia-announces-financial-results-for-fourth-quarter-and-fiscal-2025
doc_type: news
---
# NVDA Q4 FY2025 results recap

NVIDIA reported Q4 FY2025 revenue of $39.3B, up 78% year over year, with
data center revenue of $35.6B driving the beat. Management guided Q1 FY2026
revenue to roughly $43B, ahead of consensus. Blackwell contributed $11B in
its first full quarter, described as the fastest product ramp in company
history. Gross margin guidance of ~71% came in slightly below some
estimates, attributed to the Blackwell ramp mix. Management reiterated that
demand for Blackwell "significantly exceeds supply" and is expected to do
so for several quarters.
```

Authoring notes:
- Doc 2 (`10k_mdna_excerpt.md`) must be ≥8000 tokens of actual MD&A text excerpted from the public SEC filing (fetch from sec.gov, plain-text the relevant Item 7 sections). This is the long-document track载体 — do not summarize it down.
- Doc 10 (`earnings_results_future.md`) states the actual reported FY26Q1 results (revenue ~$44.1B, DC ~$39.1B, H20 charge ~$4.5B) — it exists to be *invisible* at as_of 2025-05-22.
- 事实性数字在执行时用 WebSearch/WebFetch 核对后写入；上面示例中的数字如与核对结果冲突，以核对结果为准。

- [ ] **Step 3: Freeze the bars (network, one-time)**

Run: `backend/.venv/Scripts/python backend/scripts/freeze_case_bars.py --case datasets/nvda_fy26q1 --start 2025-01-02 --end 2025-08-15`
Expected: `froze ~150 bars for NVDA -> datasets/nvda_fy26q1/bars.json` (start gives ~95 pre-as_of bars for context; end covers 40 trading days past as_of with buffer).

- [ ] **Step 4: Write the failing case-integrity test**

`backend/tests/test_nvda_case.py`:

```python
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
```

- [ ] **Step 5: Run the tests**

Run: `cd backend && .venv/Scripts/python -m pytest tests/test_nvda_case.py -q`
Expected: `4 passed` (fails loudly if the corpus is thin, the long doc is missing, or bars don't cover the outcome window)

- [ ] **Step 6: Run the dry-run against the real case**

Run: `backend/.venv/Scripts/python -m hindsight.cli dry-run --case datasets/nvda_fy26q1 --query "data center demand blackwell"`
Expected: ranked chunks (all dated ≤ 2025-05-22), a window return line, a `blocked:` lookahead line, and the audit log. The future doc `earnings_results_future` must not appear.

- [ ] **Step 7: Commit**

```bash
git add datasets backend/tests/test_nvda_case.py
git commit -m "feat(d1): NVDA FY26Q1 case dataset with frozen bars and rough corpus"
```

---

### Task 14: D1 wrap-up verification

**Files:** none new.

- [ ] **Step 1: Full test suite**

Run: `cd backend && .venv/Scripts/python -m pytest -q`
Expected: all tests pass (~35 tests across 10 files), 0 failures.

- [ ] **Step 2: Confirm CI is green**

If the repo has a GitHub remote by now: `git push` and check Actions. If not yet public, skip — CI runs on first push.

- [ ] **Step 3: Confirm D1 exit criteria from spec §10**

- [ ] CLI dry-run works on the real NVDA case (retrieval + market, no LLM)
- [ ] Leakage tests green (docs + bars channels; memory channel lands in D2)
- [ ] Probe decision recorded in `docs/eval-log.md`
- [ ] `datasets/nvda_fy26q1/` committed with frozen bars
- [ ] `.env` still untracked: `git check-ignore .env` prints `.env`

- [ ] **Step 4: Commit any stragglers and tag**

```bash
git add -A && git status --short
git commit -m "chore(d1): wrap up day-1 foundation" || true
git tag d1-complete
```

---

## Deferred to later plans (explicit, so nothing silently drops)

- **D2 plan**: agents (planner ReAct loop in the probe-decided mode, researcher, analyst, critic), orchestrator, outcome grader implementing spec §3.3 判定语义, LLM judge + failure attribution, experience library (+ memory-channel leakage tests), contamination probe, eval suite runner, `runs/` demo recording, case-3 candidate validation.
- **D3 plan**: FastAPI routes + WebSocket per spec §5, React frontend (Studio / Trace / Eval pages), README skeleton.
- **D4 plan**: Leaderboard page, datasets 2-3, judge meta-eval labeling, GIF + bilingual README, offline rehearsal.

