from __future__ import annotations

from collections import Counter
import math

from app.rag.chunking import TOKEN_PATTERN


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "can",
    "could",
    "did",
    "do",
    "does",
    "for",
    "from",
    "has",
    "have",
    "help",
    "how",
    "i",
    "in",
    "into",
    "is",
    "it",
    "may",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "should",
    "that",
    "the",
    "their",
    "them",
    "then",
    "there",
    "these",
    "this",
    "those",
    "to",
    "was",
    "we",
    "what",
    "when",
    "where",
    "who",
    "why",
    "will",
    "with",
    "you",
    "your",
    # Generic doc words that appear everywhere and cause false matches.
    "policy",
    "procedure",
    "procedures",
    "manual",
    "process",
    "processes",
    "guideline",
    "guidelines",
    "document",
    "company",
    "employee",
    "employees",
    "page",
    "section",
}


def _terms(text: str) -> Counter[str]:
    lowered = (text or "").lower().replace("-", "")
    section_mode = any(m in lowered for m in ("section", "clause", "chapter", "appendix", "article", "paragraph", "para", "page"))
    kept: list[str] = []
    for t in TOKEN_PATTERN.findall(lowered):
        if not t:
            continue
        if section_mode:
            # Keep section markers + small numbers (e.g., "section 13").
            if t in ("section", "clause", "chapter", "appendix", "article", "paragraph", "para"):
                kept.append(t)
                continue
            if t.isdigit() and 1 <= len(t) <= 4:
                kept.append(t)
                continue
        if t in _STOPWORDS:
            continue
        if len(t) < 3:
            continue
        kept.append(t)
    return Counter(kept)


def validate_context(query: str, chunks: list[object]) -> bool:
    if not chunks:
        return False

    first = chunks[0]
    score = None
    if isinstance(first, dict):
        score = first.get("score")
    else:
        score = getattr(first, "score", None)
    if isinstance(score, (int, float)):
        # Retrieval score alone can be misleading for short / generic queries.
        # Accept very strong matches directly; otherwise validate by lexical overlap below.
        if float(score) >= 0.35:
            return True

    if isinstance(first, dict):
        text = first.get("text") or first.get("excerpt", "")
    else:
        text = getattr(first, "text", None) or getattr(first, "excerpt", "")

    if not text or not query:
        return False

    query_terms = _terms(query)
    chunk_terms = _terms(text)
    if not query_terms or not chunk_terms:
        return False

    intersection = sum(min(query_terms[t], chunk_terms[t]) for t in query_terms)
    # Must share at least one meaningful term. This prevents "and/the/this" style matches.
    if intersection <= 0:
        return False

    # For section-like queries, a matching section/clause number is strong evidence.
    query_nums = [t for t in query_terms if t.isdigit()]
    if query_nums and any(n in chunk_terms for n in query_nums):
        return True

    # For very short queries (1-2 meaningful terms), presence is enough.
    # Cosine-style normalization is too strict when the chunk is long.
    if len(query_terms) <= 2:
        return True
    q_norm = math.sqrt(sum(v * v for v in query_terms.values()))
    c_norm = math.sqrt(sum(v * v for v in chunk_terms.values()))
    if q_norm == 0 or c_norm == 0:
        return False
    score = intersection / (q_norm * c_norm)
    return score >= 0.12


def is_context_sufficient(chunks: list[object]) -> bool:
    if not chunks:
        return False
    for chunk in chunks:
        if isinstance(chunk, dict):
            keyword = float(chunk.get("bm25_score", chunk.get("keyword_score", 0.0)))
            vector = float(chunk.get("vector_score", 0.0))
            reranker = float(chunk.get("reranker_score", chunk.get("final_score", 0.0)))
        else:
            keyword = float(getattr(chunk, "bm25_score", getattr(chunk, "keyword_score", 0.0)))
            vector = float(getattr(chunk, "vector_score", getattr(chunk, "score", 0.0)))
            reranker = float(getattr(chunk, "reranker_score", getattr(chunk, "score", 0.0)))
        if reranker > 0.08:
            return True
        if keyword > 0.0:
            return True
        if vector > 0.1:
            return True
    return False
