from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from app.rag.document_processor import extract_chunk_metadata
from app.rag.reranker import rerank_with_scores


def merge_and_rerank(
    query: str,
    vector_hits: list[Any],
    keyword_hits: list[dict[str, Any]],
    get_chunk_by_id: Callable[[UUID], Any],
) -> list[dict[str, Any]]:
    merged: dict[UUID, dict[str, Any]] = {}

    for hit in vector_hits:
        chunk = get_chunk_by_id(hit.chunk_id)
        if chunk is None:
            continue
        text = getattr(chunk, "text", "") or ""
        merged[hit.chunk_id] = {
            "chunk_id": hit.chunk_id,
            "text": text,
            **_metadata_fields(text),
            "vector_score": float(hit.score),
            "bm25_score": 0.0,
        }

    for item in keyword_hits:
        chunk_id = item["chunk_id"]
        chunk = get_chunk_by_id(chunk_id)
        if chunk is None:
            continue
        existing = merged.setdefault(
            chunk_id,
            {
                "chunk_id": chunk_id,
                "text": getattr(chunk, "text", "") or item.get("text", ""),
                **_metadata_fields(getattr(chunk, "text", "") or item.get("text", "")),
                "vector_score": 0.0,
                "bm25_score": 0.0,
            },
        )
        existing["bm25_score"] = float(item.get("bm25_score", 0.0))
        if not existing.get("text"):
            existing["text"] = getattr(chunk, "text", "") or item.get("text", "")

    return rerank_with_scores(query, list(merged.values()), top_k=10)


def _metadata_fields(text: str) -> dict[str, Any]:
    metadata = extract_chunk_metadata(text)
    return {
        "heading": metadata.get("heading", "General"),
        "normalized_heading": metadata.get("normalized_heading", "general"),
        "section_id": metadata.get("section_id", "general"),
        "topic": metadata.get("topic", "general"),
        "type": metadata.get("type", "policy_section"),
    }
