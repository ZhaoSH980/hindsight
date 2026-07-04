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
