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
