from __future__ import annotations

from typing import Literal

RAG_INTENT_KEYWORDS = (
    "document",
    "documents",
    "policy",
    "policies",
    "rule",
    "clause",
    "terms",
    "contract",
    "compliance",
    "procedure",
    "procedures",
    "steps",
    "process",
    "define",
    "definition",
    "what is",
    "what does",
)
LLM_INTENT_KEYWORDS = (
    "recommend",
    "advice",
    "suggest",
    "help",
    "how are you",
    "hello",
    "hi",
    "hey",
)


def route_query(query: str, bot_description: str) -> Literal["rag", "llm"]:
    normalized = (query or "").strip().lower()
    desc = (bot_description or "").strip().lower()

    if not normalized:
        return "llm"

    if any(marker in normalized for marker in LLM_INTENT_KEYWORDS):
        return "llm"

    for marker in RAG_INTENT_KEYWORDS:
        if marker in normalized:
            return "rag"

    if desc and any(marker in desc for marker in ("policy", "document", "manual", "procedure", "compliance")):
        return "rag"

    # Default to LLM for generic conversational queries.
    return "llm"
