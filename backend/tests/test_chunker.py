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


def test_oversized_blank_line_free_paragraph_is_hard_split():
    table = "\n".join(f"row {i} | val {i} | more {i}" for i in range(800))
    chunks = chunk_document(make_doc(table), target_chars=1600)
    assert len(chunks) >= 8
    assert all(len(c.text) <= 2 * 1600 for c in chunks)


def test_whitespace_only_doc_yields_no_chunks():
    assert chunk_document(make_doc("   \n\n   ")) == []
