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

