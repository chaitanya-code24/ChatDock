from __future__ import annotations

import math
from collections import Counter

from app.rag.chunking import TOKEN_PATTERN

def lexical_similarity(query: str, candidate: str) -> float:
    query_terms = Counter(TOKEN_PATTERN.findall(query.lower()))
    candidate_terms = Counter(TOKEN_PATTERN.findall(candidate.lower()))
    if not query_terms or not candidate_terms:
        return 0.0

    intersection = sum(min(query_terms[t], candidate_terms[t]) for t in query_terms)
    query_norm = math.sqrt(sum(count * count for count in query_terms.values()))
    candidate_norm = math.sqrt(sum(count * count for count in candidate_terms.values()))
    if query_norm == 0 or candidate_norm == 0:
        return 0.0
    return intersection / (query_norm * candidate_norm)
