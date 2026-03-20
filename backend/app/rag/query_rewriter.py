from __future__ import annotations

import re

GENERIC_HINTS = (
    "document",
    "policy",
    "policies",
    "procedure",
    "procedures",
    "process",
    "details",
    "section",
    "guideline",
    "guidelines",
    "practice",
    "practices",
)


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def detect_query_type(query: str) -> str:
    normalized = _normalize_space(query).lower()
    if not normalized:
        return "general"
    tokens = normalized.split()
    if any(term in normalized for term in ("explain", "describe", "go deeper", "tell me more", "more about")):
        return "explain"
    if len(tokens) <= 4 or all(token[:1].isupper() for token in _normalize_space(query).split() if token[:1].isalpha()):
        return "lookup"
    return "general"


def rewrite_query(query: str) -> str:
    normalized = (query or "").strip()
    if not normalized:
        return ""

    lowered = normalized.lower()
    query_type = detect_query_type(normalized)
    if any(phrase in lowered for phrase in ("go deeper", "explain more", "tell me more", "more about")):
        return _normalize_space(f"{normalized} in the document with detailed explanation and section context")

    if query_type == "lookup" or (len(normalized.split()) <= 5 and not any(hint in lowered for hint in GENERIC_HINTS)):
        return _normalize_space(
            f"Explain {normalized} process policy section in document including procedures and practices"
        )

    if query_type == "explain" or "what is" in lowered or "tell me about" in lowered or "explain" in lowered:
        return _normalize_space(f"{normalized} in the document with policy details procedures and section context")

    return normalized
