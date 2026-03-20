from __future__ import annotations

import hashlib
from collections import Counter

from app.core.config import settings
from app.rag.chunking import TOKEN_PATTERN
from app.rag.document_processor import extract_chunk_metadata

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None

def build_sparse_embedding(text: str) -> Counter[str]:
    return Counter(TOKEN_PATTERN.findall(_prepare_embedding_text(text).lower()))


def build_dense_embedding(text: str) -> list[float]:
    prepared_text = _prepare_embedding_text(text)
    if OpenAI is not None and settings.openai_api_key and settings.embedding_provider == "openai":
        try:
            client = OpenAI(api_key=settings.openai_api_key)
            response = client.embeddings.create(model=settings.embedding_model, input=prepared_text)
            return list(response.data[0].embedding)
        except Exception:
            pass

    # Stable local fallback embedding so vector index remains functional in dev.
    return _deterministic_embedding(prepared_text)


def _deterministic_embedding(text: str, dimensions: int = 128) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values: list[float] = []
    while len(values) < dimensions:
        for byte in digest:
            values.append((byte / 255.0) * 2.0 - 1.0)
            if len(values) == dimensions:
                break
        digest = hashlib.sha256(digest).digest()
    return values


def _prepare_embedding_text(text: str) -> str:
    metadata = extract_chunk_metadata(text)
    heading = metadata.get("heading", "General").strip()
    body = metadata.get("body", text).strip()
    if heading and body:
        return f"{heading}. {body}"
    return body or heading or (text or "")
