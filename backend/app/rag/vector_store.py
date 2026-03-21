from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.core.config import settings
from app.database.connection import get_db_session, store, use_database
from app.database.models import ChunkORM
from app.rag.document_processor import extract_chunk_metadata
from app.rag.embeddings import build_dense_embedding
from app.rag.retrieval import lexical_similarity

try:
    from qdrant_client import QdrantClient  # type: ignore
    from qdrant_client.http import models as qmodels  # type: ignore
except ImportError:  # pragma: no cover
    QdrantClient = None
    qmodels = None


def get_bot_chunks(bot_id: UUID):
    if use_database():
        for db in get_db_session():
            return db.query(ChunkORM).filter(ChunkORM.bot_id == bot_id).all()
    return [chunk for chunk in store.chunks.values() if chunk.bot_id == bot_id]


def get_chunk_by_id(chunk_id: UUID):
    if use_database():
        for db in get_db_session():
            return db.get(ChunkORM, chunk_id)
    return store.chunks.get(chunk_id)


@dataclass(slots=True)
class SearchResult:
    chunk_id: UUID
    score: float


class VectorStore:
    def __init__(self) -> None:
        self._client = None
        if QdrantClient is not None and qmodels is not None:
            try:
                client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
                self._ensure_collection(client)
                self._client = client
            except Exception:
                self._client = None

    def upsert_bot_chunks(self, bot_id: UUID) -> None:
        chunks = get_bot_chunks(bot_id)
        if not chunks or self._client is None or qmodels is None:
            return

        points = []
        for chunk in chunks:
            metadata = extract_chunk_metadata(chunk.text)
            points.append(
                qmodels.PointStruct(
                    id=str(chunk.id),
                    vector=build_dense_embedding(chunk.text),
                    payload={
                        "bot_id": str(bot_id),
                        "document_id": str(chunk.document_id),
                        "text": chunk.text,
                        "heading": metadata["heading"],
                        "normalized_heading": metadata.get("normalized_heading", metadata["heading"].lower()),
                        "topic": metadata["topic"],
                        "type": metadata["type"],
                    },
                )
            )
        self._client.upsert(collection_name=settings.qdrant_collection, points=points)

    def search(self, bot_id: UUID, query: str, limit: int) -> list[SearchResult]:
        if self._client is not None and qmodels is not None:
            try:
                query_vector = build_dense_embedding(query)
                points = self._client.search(
                    collection_name=settings.qdrant_collection,
                    query_vector=query_vector,
                    limit=limit,
                    query_filter=qmodels.Filter(
                        must=[qmodels.FieldCondition(key="bot_id", match=qmodels.MatchValue(value=str(bot_id)))]
                    ),
                )
                results = [SearchResult(chunk_id=UUID(str(point.id)), score=float(point.score)) for point in points]
                # If vector search looks unconfident (common in dev fallback embeddings),
                # fall back to lexical scoring to avoid returning irrelevant context.
                if results and results[0].score >= 0.15:
                    return results
            except Exception:
                pass

        chunks = get_bot_chunks(bot_id)
        ranked = sorted(
            ((lexical_similarity(query, chunk.text), chunk.id) for chunk in chunks),
            key=lambda item: item[0],
            reverse=True,
        )
        return [SearchResult(chunk_id=chunk_id, score=score) for score, chunk_id in ranked[:limit] if score > 0]

    def _ensure_collection(self, client: Any) -> None:
        existing = [col.name for col in client.get_collections().collections]
        if settings.qdrant_collection in existing:
            return
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=qmodels.VectorParams(size=128, distance=qmodels.Distance.COSINE),
        )


vector_store = VectorStore()
