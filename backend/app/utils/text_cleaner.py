from __future__ import annotations

import re


WHITESPACE = re.compile(r"\s+")
# Only merge OCR-style single-letter spacing: "P r o p o s a l" -> "Proposal".
# Avoid merging real word boundaries like "ChatDock has" -> "ChatDockhas".
LETTER_GAP = re.compile(r"\b([a-zA-Z])\s+([a-zA-Z])\b")


def clean_text(text: str) -> str:
    cleaned = WHITESPACE.sub(" ", text).strip()
    # Multiple passes collapse sequences of single-letter tokens.
    for _ in range(12):
        next_cleaned = LETTER_GAP.sub(r"\1\2", cleaned)
        if next_cleaned == cleaned:
            break
        cleaned = next_cleaned
    cleaned = re.sub(r"([Pp])\s+roposal", r"\1roposal", cleaned)
    return cleaned

