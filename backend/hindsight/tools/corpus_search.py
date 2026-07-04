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
