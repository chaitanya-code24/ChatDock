from __future__ import annotations

import re


TOKEN_PATTERN = re.compile(r"\w+")


def chunk_text(text: str, chunk_size_tokens: int, chunk_overlap: int) -> list[str]:
    words = TOKEN_PATTERN.findall(text)
    if not words:
        return []

    step = max(1, chunk_size_tokens - chunk_overlap)
    chunks: list[str] = []
    for start in range(0, len(words), step):
        end = start + chunk_size_tokens
        section = words[start:end]
        if section:
            chunks.append(" ".join(section))
        if end >= len(words):
            break
    return chunks


def estimate_token_count(text: str) -> int:
    return max(1, len(TOKEN_PATTERN.findall(text)))


def chunk_preserving_section(text: str, max_tokens: int = 500) -> list[str]:
    normalized = (text or "").strip()
    if not normalized:
        return []

    if estimate_token_count(normalized) <= max_tokens:
        return [normalized]

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+|\n+", normalized) if part.strip()]
    if not sentences:
        return [normalized]

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for sentence in sentences:
        sentence_tokens = estimate_token_count(sentence)
        if current and current_tokens + sentence_tokens > max_tokens:
            chunks.append(" ".join(current).strip())
            current = [sentence]
            current_tokens = sentence_tokens
        else:
            current.append(sentence)
            current_tokens += sentence_tokens
    if current:
        chunks.append(" ".join(current).strip())
    return chunks

