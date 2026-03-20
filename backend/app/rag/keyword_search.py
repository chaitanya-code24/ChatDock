from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any


def normalize(text: str) -> str:
    lowered = (text or "").lower()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return lowered


def normalize_query(query: str) -> str:
    return normalize(query)


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", normalize(text))


def keyword_search(query: str, chunks: list[Any], limit: int = 20) -> list[dict[str, Any]]:
    query_tokens = tokenize(query)
    if not query_tokens:
        return []

    tokenized_docs = [_document_terms(chunk) for chunk in chunks]
    doc_count = len(tokenized_docs)
    avgdl = sum(len(doc) for doc in tokenized_docs) / max(doc_count, 1)
    doc_freq = Counter()
    for doc_tokens in tokenized_docs:
        for token in set(doc_tokens):
            doc_freq[token] += 1

    ranked: list[dict[str, Any]] = []
    for chunk, doc_tokens in zip(chunks, tokenized_docs):
        bm25_score = _bm25_score(query_tokens, doc_tokens, doc_freq, doc_count, avgdl)
        if bm25_score <= 0:
            continue
        ranked.append(
            {
                "chunk_id": getattr(chunk, "id"),
                "text": getattr(chunk, "text", "") or "",
                "bm25_score": bm25_score,
            }
        )
    ranked.sort(key=lambda item: float(item["bm25_score"]), reverse=True)
    return ranked[:limit]


def _document_terms(chunk: Any) -> list[str]:
    return tokenize(getattr(chunk, "text", "") or "")


def _bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    doc_freq: Counter[str],
    doc_count: int,
    avgdl: float,
    *,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    score = 0.0
    doc_len = len(doc_tokens)
    for token in query_tokens:
        if token not in tf:
            continue
        df = doc_freq.get(token, 0)
        idf = math.log(1 + ((doc_count - df + 0.5) / (df + 0.5)))
        freq = tf[token]
        denom = freq + k1 * (1 - b + b * (doc_len / max(avgdl, 1e-9)))
        score += idf * ((freq * (k1 + 1)) / max(denom, 1e-9))
    return score
