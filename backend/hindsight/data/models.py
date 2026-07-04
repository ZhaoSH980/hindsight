"""Core data records shared across the backend."""
from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class Bar(BaseModel):
    """One daily OHLCV bar. Prices are split/dividend adjusted (auto_adjust=True)."""

    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


class CaseMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

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
