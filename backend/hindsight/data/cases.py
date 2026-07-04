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
