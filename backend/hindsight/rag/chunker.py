"""Greedy paragraph packer: split on blank lines, start fresh at headings.

A paragraph larger than 4x target_chars (typically a table pasted without
blank lines) is hard-split on line boundaries; a paragraph between 1x and
4x target stays intact as one oversized chunk (never split mid-paragraph).
"""
from __future__ import annotations

import re

from hindsight.data.models import Chunk, Document

_HEADING = re.compile(r"^#{1,6}\s")


def _split_oversized(para: str, target_chars: int) -> list[str]:
    """Hard-split a blank-line-free paragraph (e.g. a pasted table) on line
    boundaries. A single line longer than target_chars stays intact."""
    if len(para) <= 4 * target_chars:
        return [para]
    pieces: list[str] = []
    current: list[str] = []
    size = 0
    for line in para.splitlines():
        if current and size + len(line) > target_chars:
            pieces.append("\n".join(current))
            current, size = [], 0
        current.append(line)
        size += len(line)
    if current:
        pieces.append("\n".join(current))
    return pieces


def chunk_document(doc: Document, target_chars: int = 1600) -> list[Chunk]:
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", doc.text) if p.strip()]
    paragraphs = [
        piece for p in raw_paragraphs for piece in _split_oversized(p, target_chars)
    ]
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
