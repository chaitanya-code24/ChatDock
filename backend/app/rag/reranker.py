from __future__ import annotations

import json
import math
from collections import Counter
from typing import Any, Iterable

from app.core.config import settings
from app.rag.keyword_search import normalize, tokenize

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None


def rerank_with_scores(query: str, candidates: list[dict[str, Any]], top_k: int = 10) -> list[dict[str, Any]]:
    if not candidates:
        return []

    scored = _model_scores(query, candidates)
    if scored is None:
        scored = _fallback_scores(query, candidates)

    ranked: list[dict[str, Any]] = []
    for candidate, score in zip(candidates, scored):
        enriched = dict(candidate)
        enriched["reranker_score"] = float(score)
        enriched["final_score"] = float(score)
        ranked.append(enriched)

    ranked.sort(key=lambda item: float(item["final_score"]), reverse=True)
    return ranked[:top_k]


def rerank_chunks(query: str, chunks: Iterable[object], top_k: int = 3) -> list[object]:
    candidates = []
    originals = []
    for index, chunk in enumerate(chunks):
        text = ""
        if isinstance(chunk, dict):
            text = chunk.get("text") or chunk.get("excerpt", "")
        else:
            text = getattr(chunk, "text", None) or getattr(chunk, "excerpt", "")
        if not text:
            continue
        candidates.append({"text": text, "_source_index": index})
        originals.append(chunk)

    scored = rerank_with_scores(query, candidates, top_k=top_k)
    selected: list[object] = []
    for item in scored:
        idx = int(item["_source_index"])
        selected.append(originals[idx])
    return selected


def _model_scores(query: str, candidates: list[dict[str, Any]]) -> list[float] | None:
    client = _get_llm_client()
    if client is None:
        return None

    payload = [
        {
            "id": index,
            "text": _truncate_text(str(candidate.get("text", "")), 1200),
        }
        for index, candidate in enumerate(candidates)
    ]
    prompt = (
        "You are a retrieval reranker. Score each candidate passage for relevance to the query.\n"
        "Return strict JSON as a list of objects with keys: id, score.\n"
        "Score must be between 0 and 1.\n"
        "Higher means more relevant.\n\n"
        f"Query: {query}\n\n"
        f"Candidates: {json.dumps(payload, ensure_ascii=False)}"
    )
    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=400,
            temperature=0.0,
            top_p=1.0,
            messages=[
                {"role": "system", "content": "Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
        )
        content = (response.choices[0].message.content or "").strip()
        parsed = json.loads(content)
        score_map = {int(item["id"]): float(item["score"]) for item in parsed if "id" in item and "score" in item}
        return [score_map.get(index, 0.0) for index in range(len(candidates))]
    except Exception:
        return None


def _fallback_scores(query: str, candidates: list[dict[str, Any]]) -> list[float]:
    return [_semantic_score(query, str(candidate.get("text", ""))) for candidate in candidates]


def _semantic_score(query: str, text: str) -> float:
    query_terms = Counter(tokenize(normalize(query)))
    text_terms = Counter(tokenize(normalize(text)))
    if not query_terms or not text_terms:
        return 0.0
    intersection = sum(min(query_terms[token], text_terms[token]) for token in query_terms)
    if intersection <= 0:
        return 0.0
    q_norm = math.sqrt(sum(value * value for value in query_terms.values()))
    t_norm = math.sqrt(sum(value * value for value in text_terms.values()))
    if q_norm == 0 or t_norm == 0:
        return 0.0
    return intersection / (q_norm * t_norm)


def _truncate_text(text: str, max_chars: int) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= max_chars:
        return normalized
    return normalized[: max_chars - 3].rstrip() + "..."


def _get_llm_client():
    if OpenAI is None:
        return None
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAI(api_key=settings.openai_api_key)
    if settings.llm_provider == "groq" and settings.groq_api_key:
        return OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
    return None
