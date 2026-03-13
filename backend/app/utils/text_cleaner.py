from __future__ import annotations

import re


WHITESPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    return WHITESPACE.sub(" ", text).strip()

