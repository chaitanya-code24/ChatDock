from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone, timedelta
from collections import Counter, defaultdict
from typing import Iterable, Literal
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import delete, func, select

from app.core.cache import cache_service
from app.core.conversation import ConversationEntry, conversation_service
from app.core.config import settings
from app.database.connection import get_db_session, use_database, store
from app.database.models import BotORM, ChatLogORM, ChatThreadORM, ChunkORM, DocumentORM
from app.models.bot_model import BotRecord
from app.models.chat_model import ChatLogRecord, ChatThreadRecord
from app.rag.document_processor import extract_chunk_metadata
from app.rag.vector_store import get_bot_chunks, get_chunk_by_id, vector_store
from app.rag.chunking import TOKEN_PATTERN
from app.rag.hybrid_ranker import merge_and_rerank
from app.rag.keyword_search import keyword_search, normalize_query, tokenize
from app.rag.query_router import route_query
from app.rag.query_rewriter import detect_query_type, rewrite_query
from app.rag.reranker import rerank_chunks
from app.rag.context_validator import validate_context
from app.rag.retrieval import lexical_similarity
from app.schemas.chat_schema import AnalyticsOverview, BotQueryStat, ChatThreadMessage, ChatThreadSummary, SourceChunk, TopQuery

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None


class ChatService:
    CACHE_SCHEMA_VERSION = "v18"

    def answer(
        self,
        user_id: UUID,
        bot_id: UUID,
        message: str,
        *,
        conversation_id: UUID | None = None,
        bypass_cache: bool = False,
    ) -> tuple[str, bool, list[SourceChunk], list[str], UUID]:
        logs: list[str] = []
        bot = self._get_bot_for_user(user_id, bot_id)
        bot_name = bot.bot_name
        bot_description = bot.description
        bot_has_docs = self._bot_has_documents(bot_id)
        if message.strip().startswith("!nocache"):
            bypass_cache = True
            message = message.strip()[8:].strip()
            logs.append("Bypass cache requested.")

        conv_id = conversation_id or uuid4()
        conv_key = f"{user_id}:{bot_id}:{conv_id}"
        self._ensure_thread(user_id, bot_id, conv_id, message)
        history = self._load_thread_history(user_id, bot_id, conv_id)
        logs.append(f"Conversation id: {conv_id} (history: {len(history)} messages)")

        intent = self._detect_intent(message)
        logs.append(f"Detected intent: {intent}")

        # Metadata question: list document names (this is not in chunk text, so don't force "not found").
        if self._is_document_name_query(message):
            docs = self._list_documents_for_bot(bot_id)
            if not docs:
                answer = f"### {bot_name} answer\n\nNo documents are uploaded for this bot yet."
            else:
                answer = f"### {bot_name} answer\n\nUploaded documents:\n" + "\n".join(f"- {name}" for name in docs)
            conversation_service.append(conv_key, "user", message)
            conversation_service.append(conv_key, "assistant", answer)
            self._log_query(user_id, bot_id, conv_id, message, answer, cached=False)
            return answer, False, [], logs, conv_id
        if intent == "greeting":
            has_docs = self._bot_has_documents(bot_id)
            if has_docs:
                desc = (bot_description.strip() + "\n\n") if bot_description else ""
                answer = (
                    f"{(bot.greeting_message or bot_name).strip()}\n"
                    "I answer questions using your uploaded documents.\n\n"
                    f"{desc}"
                    "Ask a specific question about your uploaded documents. "
                    "If the answer is not present in the documents, I will say so."
                )
            else:
                answer = (
                    f"{(bot.greeting_message or bot_name).strip()}\n"
                    "Upload a document first, then ask questions and I’ll answer from that content.\n\n"
                    "Examples:\n"
                    "- \"What is the return policy?\"\n"
                    "- \"How long do refunds take?\""
                )
            conversation_service.append(conv_key, "user", message)
            conversation_service.append(conv_key, "assistant", answer)
            self._log_query(user_id, bot_id, conv_id, message, answer, cached=False)
            return answer, False, [], logs, conv_id

        # Simple RAG only: use uploaded docs to answer. No extra routing/loops.
        if not bot_has_docs:
            answer = (
                f"### {bot_name} answer\n\n"
                "Upload a document first, then ask questions and I’ll answer from that content."
            )
            conversation_service.append(conv_key, "user", message)
            conversation_service.append(conv_key, "assistant", answer)
            self._log_query(user_id, bot_id, conv_id, message, answer, cached=False)
            return answer, False, [], logs, conv_id

        return self._simple_rag_answer(
            user_id=user_id,
            bot_id=bot_id,
            bot=bot,
            message=message,
            conv_key=conv_key,
            conv_id=conv_id,
            history=history,
            bypass_cache=bypass_cache,
            logs=logs,
        )

    def _simple_rag_answer(
        self,
        *,
        user_id: UUID,
        bot_id: UUID,
        bot: BotRecord,
        message: str,
        conv_key: str,
        conv_id: UUID,
        history: list[ConversationEntry],
        bypass_cache: bool,
        logs: list[str],
    ) -> tuple[str, bool, list[SourceChunk], list[str], UUID]:
        # Light follow-up: if user says "explain more", include last topic in retrieval query.
        followup = self._is_followup_message(message.lower().strip())
        last_topic = self._find_last_topic_user_message(history).strip() if history else ""
        query = (f"{last_topic}\n{message}".strip() if followup and last_topic else message).strip()
        if query != message:
            logs.append("Follow-up: appended last topic for retrieval.")

        conversation_service.append(conv_key, "user", message)
        sources, normalized_query = self._search(bot_id=bot_id, message=query, logs=logs)
        if not sources:
            answer = self._not_found_in_docs_answer(bot.bot_name, bot.fallback_behavior, bot.description)
            conversation_service.append(conv_key, "assistant", answer)
            self._log_query(user_id, bot_id, conv_id, message, answer, cached=False)
            return answer, False, [], logs, conv_id

        section_ids = [extract_chunk_metadata(source.excerpt).get("section_id", str(source.chunk_id)) for source in sources]
        cache_key = self._cache_key(user_id, bot_id, normalized_query, section_ids)
        if not bypass_cache:
            cached_response = cache_service.get(cache_key)
            if cached_response is not None:
                logs.append("Cache hit.")
                conversation_service.append(conv_key, "assistant", cached_response)
                self._log_query(user_id, bot_id, conv_id, message, cached_response, cached=True)
                return cached_response, True, sources, logs, conv_id

        response = self._rag_markdown_answer(bot, message, sources, history=history)
        response = (response or "").strip()
        if not response:
            response = self._build_markdown_fallback(
                bot.bot_name,
                message,
                sources,
                fallback_behavior=bot.fallback_behavior,
                bot_description=bot.description,
            )
        response = self._normalize_markdown_output(response)

        conversation_service.append(conv_key, "assistant", response)
        cacheable = self._is_cacheable(response, sources)
        if cacheable and not bypass_cache:
            logs.append("Caching response.")
            cache_service.set(cache_key, response)
        self._log_query(user_id, bot_id, conv_id, message, response, cached=False)
        return response, False, sources, logs, conv_id

    def _search(self, bot_id: UUID, message: str, logs: list[str] | None = None) -> tuple[list[SourceChunk], str]:
        logs = logs if logs is not None else []
        normalized_query = normalize_query(message)
        rewritten_query = rewrite_query(message)
        query_type = detect_query_type(message)
        all_chunks = get_bot_chunks(bot_id)
        logs.append(f"Normalized query: {normalized_query}")
        self.debug_find_chunk(message, all_chunks, logs)
        heading_matches = self._heading_search(normalized_query, all_chunks, logs)
        if heading_matches:
            logs.append(f"Heading-first retrieval matched {len(heading_matches)} chunk(s).")
            return self._build_sources_from_chunks(heading_matches, message, logs), normalized_query

        vector_hits = vector_store.search(bot_id=bot_id, query=rewritten_query, limit=20)
        keyword_hits = keyword_search(message, all_chunks, limit=20)
        ranked_hits = merge_and_rerank(message, vector_hits, keyword_hits, get_chunk_by_id)
        logs.append(f"Rewritten query: {rewritten_query}")
        logs.append(f"Query type: {query_type}")
        logs.append(f"Vector hits: {len(vector_hits)}")
        logs.append(f"BM25 hits: {len(keyword_hits)}")
        for index, item in enumerate(keyword_hits[:5]):
            logs.append(
                f"BM25 {index + 1}: chunk={item['chunk_id']} score={float(item.get('bm25_score', 0.0)):.3f} "
                f"heading={item.get('heading', 'General')}"
            )
        for i, hit in enumerate(vector_hits[:12]):
            chunk = get_chunk_by_id(hit.chunk_id)
            if chunk is None:
                continue
            preview = chunk.text[:500]
            print(f"\n===== HIT {i} =====")
            print(f"Score: {hit.score}")
            print(preview)
            logs.append(f"===== HIT {i} =====")
            logs.append(f"Score: {hit.score}")
            logs.append(preview)

        self._log_hybrid_debug(rewritten_query, query_type, ranked_hits, logs)
        if not ranked_hits:
            logs.append("No merged results. Retrying retrieval with BM25-only section grouping.")
            relaxed_hits = keyword_search(normalized_query, all_chunks, limit=30)
            ranked_hits = [
                {
                    "chunk_id": item["chunk_id"],
                    "final_score": float(item.get("bm25_score", 0.0)),
                    "bm25_score": float(item.get("bm25_score", 0.0)),
                }
                for item in relaxed_hits
            ]
            if not ranked_hits:
                return [], normalized_query
        chunk_matches = []
        for item in ranked_hits[: max(settings.max_context_chunks * 3, 8)]:
            chunk = get_chunk_by_id(item["chunk_id"])
            if chunk is not None:
                chunk_matches.append((chunk, float(item["final_score"])))
        return self._build_sources_from_chunks(chunk_matches, message, logs), normalized_query

    def _build_sources_from_chunks(self, chunks: list[tuple[object, float]], query: str, logs: list[str] | None = None) -> list[SourceChunk]:
        logs = logs if logs is not None else []
        grouped: dict[str, dict[str, object]] = {}
        for chunk, score in chunks:
            metadata = extract_chunk_metadata(getattr(chunk, "text", ""))
            section_id = metadata.get("section_id", str(chunk.id))
            entry = grouped.setdefault(section_id, {"score": 0.0, "chunks": []})
            entry["score"] = max(float(entry["score"]), float(score))
            entry["chunks"].append(chunk)

        selected = sorted(grouped.items(), key=lambda item: float(item[1]["score"]), reverse=True)[: min(settings.max_context_chunks, 3)]
        logs.append(f"Selected section_ids: {[section_id for section_id, _ in selected]}")

        sources: list[SourceChunk] = []
        for section_id, entry in selected:
            section_chunks = entry["chunks"]
            if not section_chunks:
                continue
            ordered_chunks = sorted(section_chunks, key=lambda item: str(item.id))
            primary_chunk = ordered_chunks[0]
            document = self._get_document(primary_chunk.document_id)
            if document is None:
                continue
            combined_text = "\n\n".join(getattr(item, "text", "") for item in ordered_chunks)
            sources.append(
                SourceChunk(
                    document_id=primary_chunk.document_id,
                    document_name=document.file_name,
                    chunk_id=primary_chunk.id,
                    score=round(float(entry["score"]), 3),
                    excerpt=combined_text,
                )
            )
        return sources

    @staticmethod
    def _heading_search(normalized_query: str, chunks: list[object], logs: list[str]) -> list[tuple[object, float]]:
        query_tokens = tokenize(normalized_query)
        if not query_tokens:
            return []

        matches: list[tuple[object, float]] = []
        for chunk in chunks:
            metadata = extract_chunk_metadata(getattr(chunk, "text", ""))
            normalized_heading = normalize_query(metadata.get("normalized_heading", ""))
            heading_tokens = tokenize(normalized_heading)
            if not heading_tokens:
                continue
            overlap = sum(1 for token in query_tokens if token in heading_tokens)
            overlap_ratio = overlap / max(len(query_tokens), len(heading_tokens))
            if overlap_ratio >= 0.7:
                matches.append((chunk, overlap_ratio))

        matches.sort(key=lambda item: item[1], reverse=True)
        for index, (chunk, score) in enumerate(matches[:5]):
            metadata = extract_chunk_metadata(getattr(chunk, "text", ""))
            logs.append(f"HEADING MATCH {index + 1}: heading={metadata.get('heading')} score={score:.3f}")
        return matches

    @staticmethod
    def debug_find_chunk(query: str, chunks: list[object], logs: list[str] | None = None) -> None:
        logs = logs if logs is not None else []
        query_tokens = [token for token in TOKEN_PATTERN.findall((query or "").lower()) if len(token) > 2]
        if not query_tokens:
            return
        logs.append("DEBUG FIND CHUNK:")
        found = 0
        for chunk in chunks:
            text = getattr(chunk, "text", "")
            lowered = text.lower()
            if not any(token in lowered for token in query_tokens):
                continue
            metadata = extract_chunk_metadata(text)
            preview = " ".join(metadata.get("body", text).split())[:220]
            line = f"heading={metadata.get('heading')} preview={preview}"
            print(line)
            logs.append(line)
            found += 1
            if found >= 10:
                break
        if found == 0:
            logs.append("No stored chunk contained the query terms.")

    @staticmethod
    def _log_hybrid_debug(query: str, query_type: str, ranked_hits: list[dict[str, object]], logs: list[str]) -> None:
        print(f"QUERY [hybrid]: {query}")
        print(f"QUERY TYPE: {query_type}")
        print("TOP CHUNKS:")
        logs.append(f"QUERY TYPE: {query_type}")
        logs.append("TOP CHUNKS:")
        for index, item in enumerate(ranked_hits[:5]):
            preview = " ".join(str(item.get("text", "")).split())[:200]
            line = (
                f"rank={index + 1} vector={float(item.get('vector_score', 0.0)):.3f} "
                f"bm25={float(item.get('bm25_score', 0.0)):.3f} "
                f"reranker={float(item.get('reranker_score', item.get('final_score', 0.0))):.3f} "
                f"final={float(item.get('final_score', 0.0)):.3f} "
                f"chunk={item.get('chunk_id')} preview={preview}"
            )
            print(line)
            logs.append(line)

    def _generate_answer(
        self,
        bot_name: str,
        message: str,
        sources: Iterable[SourceChunk],
        *,
        history: list[ConversationEntry] | None = None,
    ) -> str:
        source_list = list(sources)
        if not source_list:
            return self._not_found_in_docs_answer(bot_name)

        bot = BotRecord(
            id=uuid4(),
            user_id=uuid4(),
            bot_name=bot_name,
            description=None,
            created_at=datetime.now(timezone.utc),
        )
        answer_md = self._rag_markdown_answer(bot, message, source_list, history=history or [])
        if self._validate_answer(answer_md):
            return answer_md
        return self._build_markdown_fallback(bot_name, message, source_list)

    def _rag_markdown_answer(self, bot: BotRecord, message: str, source_list: list[SourceChunk], *, history: list[ConversationEntry]) -> str:
        llm_client = self._get_llm_client()
        if llm_client is None:
            return self._build_markdown_fallback(
                bot.bot_name,
                message,
                source_list,
                fallback_behavior=bot.fallback_behavior,
                bot_description=bot.description,
            )

        context = "\n\n".join(
            f"[Section: {extract_chunk_metadata(source.excerpt).get('heading', 'General')}]\n\n{source.excerpt}"
            for source in source_list[: min(settings.max_context_chunks, 3)]
        )
        print("FINAL CONTEXT SENT TO LLM:")
        print(context[:2000])
        history_block = self._history_block(history)
        system_prompt = (
            "You are a document assistant.\n"
            "Answer using ONLY the provided context.\n\n"
            "Rules:\n"
            "* Give complete answer\n"
            "* Use all relevant information\n"
            "* Do NOT say 'not found' if partial info exists\n"
            "* Do NOT include reasoning\n"
            f"* Keep the tone {bot.tone}\n"
            f"* Keep the answer length {bot.answer_length}\n\n"
            "Format:\n"
            "Title\n\n"
            "Key Points\n"
            "* ...\n\n"
            "Details\n"
            "1. ...\n"
            "2. ...\n\n"
            "Summary"
        )
        if bot.system_prompt:
            system_prompt = f"{system_prompt}\n\nAdditional bot instructions:\n{bot.system_prompt.strip()}"
        user_prompt = (
            f"{history_block}\n\nContext:\n{context}\n\nQuestion:\n{message}\n\n"
            "Respond with markdown only using the requested structure."
        )
        try:
            content = self._generate_llm_answer(
                llm_client,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
            )
            if not content:
                raise RuntimeError("Empty LLM response")
            return self._normalize_markdown_output(content)
        except Exception:
            return self._build_markdown_fallback(
                bot.bot_name,
                message,
                source_list,
                fallback_behavior=bot.fallback_behavior,
                bot_description=bot.description,
            )

    def _validate_answer(self, response: str) -> bool:
        if not response or len(response) < 50:
            return False
        # Allow explicit "not found in docs" responses; those are valid outcomes for RAG.
        if "not available" in response.lower():
            return False
        return True

    @staticmethod
    def _detect_intent(message: str) -> Literal["document", "recommendation", "greeting", "definition", "steps", "policy"]:
        normalized = message.lower().strip()
        # Greeting detection must be word-boundary based.
        # A naive substring match makes "hi" match "this" and routes real questions incorrectly.
        if (
            re.search(r"(?<![a-z])(?:hi|hey|hello)(?![a-z])", normalized) is not None
            or normalized.startswith("good morning")
            or normalized.startswith("good evening")
            or "how can you help" in normalized
            or "what can you do" in normalized
            or re.search(r"(?<![a-z])help me(?![a-z])", normalized) is not None
        ):
            return "greeting"
        if any(word in normalized for word in ("suggest", "recommend", "should i", "what is the best", "for my child", "advice")):
            return "recommendation"
        if any(marker in normalized for marker in ("what is", "what does", "means", "define", "definition")):
            return "definition"
        if any(marker in normalized for marker in ("step", "steps", "process", "procedure", "how to", "how do i", "how should")):
            return "steps"
        if any(marker in normalized for marker in ("policy", "rule", "guideline", "handle", "handled", "compliance")):
            return "policy"
        return "document"

    @staticmethod
    def _not_found_in_docs_answer(bot_name: str, fallback_behavior: str = "strict", bot_description: str | None = None) -> str:
        if fallback_behavior == "helpful":
            prefix = f"{bot_description.strip()}\n\n" if bot_description else ""
            return (
                f"### {bot_name} answer\n\n"
                f"{prefix}"
                "I could not find a clear answer to this question in the uploaded documents.\n\n"
                "_Not found in uploaded documents._"
            )
        return (
            f"### {bot_name} answer\n\n"
            "Information not found in document.\n\n"
            "_Not found in uploaded documents._"
        )

    @staticmethod
    def _compress_sources_for_llm(source_list: list[SourceChunk]) -> str:
        blocks: list[str] = []
        for source in source_list:
            metadata = extract_chunk_metadata(source.excerpt)
            heading = metadata.get("heading", "General")
            body = metadata.get("body", source.excerpt)
            bullets = ChatService._compress_text_to_bullets(body, max_points=3, max_chars=420)
            if not bullets:
                continue
            block = [f"[Section: {heading}]"]
            block.extend(f"* {bullet}" for bullet in bullets)
            blocks.append("\n".join(block))
        return "\n\n".join(blocks)

    @staticmethod
    def _compress_text_to_bullets(text: str, *, max_points: int = 3, max_chars: int = 420) -> list[str]:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if s.strip()]
        bullets: list[str] = []
        seen: set[str] = set()
        for sentence in sentences:
            cleaned = ChatService._clean_unit(sentence, max_len=180)
            normalized = cleaned.lower()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            bullets.append(cleaned)
            if len(bullets) >= max_points or sum(len(b) for b in bullets) >= max_chars:
                break
        return bullets

    def _generate_llm_answer(self, llm_client, *, system_prompt: str, user_prompt: str, temperature: float) -> str:
        response = llm_client.chat.completions.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_output_tokens,
            temperature=temperature,
            top_p=1.0,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    def _verify_answer_with_context(self, llm_client, context: str, message: str, answer: str) -> bool:
        try:
            response = llm_client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=10,
                temperature=0.0,
                top_p=1.0,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Check whether the answer is supported by the context.\n\n"
                            "Rules:\n"
                            "- Consider both direct and implied information.\n"
                            "- If the answer logically follows, mark it as supported.\n"
                            "- Only reject if clearly incorrect or unrelated.\n\n"
                            "Return ONLY:\n"
                            "- True\n"
                            "- False"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion:\n{message}\n\nDraft answer:\n{answer}",
                    },
                ],
            )
            verified = (response.choices[0].message.content or "").strip().lower()
            return verified == "true"
        except Exception:
            return True

    @staticmethod
    def _is_document_name_query(message: str) -> bool:
        q = (message or "").lower().strip()
        if not q:
            return False
        patterns = (
            "name of doc",
            "name of document",
            "document names",
            "document name",
            "which document",
            "what documents",
            "list documents",
            "show documents",
            "uploaded documents",
            "uploaded document",
            "what pdf",
            "which pdf",
        )
        if any(p in q for p in patterns):
            return True
        return re.search(r"\b(list|show)\b.*\b(uploaded )?document(s)?\b", q) is not None

    @staticmethod
    def _list_documents_for_bot(bot_id: UUID) -> list[str]:
        if use_database():
            for db in get_db_session():
                rows = (
                    db.execute(
                        select(DocumentORM.file_name).where(DocumentORM.bot_id == bot_id).order_by(DocumentORM.uploaded_at.desc())
                    )
                    .scalars()
                    .all()
                )
                return [r for r in rows if r]
        docs = [d.file_name for d in store.documents.values() if d.bot_id == bot_id]
        # keep stable ordering
        return sorted([d for d in docs if d])

    @staticmethod
    def _lexical_sources(bot_id: UUID, query: str, *, limit: int = 12, top_k: int = 4) -> list[SourceChunk]:
        chunks = get_bot_chunks(bot_id)
        scored = sorted(
            ((lexical_similarity(query, c.text), c) for c in chunks),
            key=lambda item: item[0],
            reverse=True,
        )
        best = [item for item in scored[:limit] if item[0] > 0]
        sources: list[SourceChunk] = []
        for score, chunk in best:
            document = ChatService._get_document(chunk.document_id)
            if document is None:
                continue
            sources.append(
                SourceChunk(
                    document_id=chunk.document_id,
                    document_name=document.file_name,
                    chunk_id=chunk.id,
                    score=round(float(score), 3),
                    excerpt=ChatService._excerpt_for_query(chunk.text, query, max_len=900),
                )
            )
        reranked = rerank_chunks(query, sources, top_k=top_k)
        if not reranked:
            return sources[:top_k]
        return reranked[:top_k]

    @staticmethod
    def _excerpt_for_query(text: str, query: str, *, max_len: int = 900) -> str:
        """
        Build an excerpt around query terms (instead of always taking the start of the chunk).
        This improves relevance validation and gives the LLM the right snippet.
        """
        raw = (text or "").strip()
        if not raw:
            return ""

        q = (query or "").lower().replace("-", "")
        # Keep only meaningful terms for locating a window.
        stop = {
            "a",
            "an",
            "and",
            "are",
            "as",
            "at",
            "be",
            "by",
            "for",
            "from",
            "how",
            "i",
            "in",
            "is",
            "it",
            "of",
            "on",
            "or",
            "that",
            "the",
            "this",
            "to",
            "was",
            "what",
            "when",
            "where",
            "who",
            "why",
            "with",
            "you",
            "your",
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
        section_mode = any(m in q for m in ("section", "clause", "chapter", "appendix", "article", "paragraph", "para", "page"))
        raw_terms = [t for t in TOKEN_PATTERN.findall(q) if t]
        if section_mode:
            # Prefer finding a section-like pattern first.
            nums = [t for t in raw_terms if t.isdigit() and 1 <= len(t) <= 4]
            if nums:
                pat = re.compile(
                    rf"(?:section|clause|chapter|appendix|article|para|paragraph)?\s*{re.escape(nums[0])}\b",
                    re.IGNORECASE,
                )
                m = pat.search(raw)
                if m:
                    hit_at = m.start()
                    lead = 220
                    tail = max_len - lead
                    start = max(0, hit_at - lead)
                    end = min(len(raw), hit_at + max(120, tail))
                    snippet = raw[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(raw):
                        snippet = snippet + "..."
                    return snippet

        terms = [t for t in raw_terms if t and t not in stop and (len(t) >= 3 or (section_mode and t.isdigit()))]
        lowered = raw.lower().replace("-", "")

        hit_at = -1

        # Prefer multi-word phrase matches from the query (e.g., "service level management").
        if len(terms) >= 2:
            max_n = min(4, len(terms))
            for n in range(max_n, 1, -1):
                for i in range(0, len(terms) - n + 1):
                    phrase = " ".join(terms[i : i + n]).strip()
                    if not phrase:
                        continue
                    pos = lowered.find(phrase)
                    if pos != -1:
                        hit_at = pos
                        break
                if hit_at != -1:
                    break

        # If no phrase matched, pick the rarest matched term to avoid generic anchors like "management".
        if hit_at == -1 and terms:
            best_pos = None
            best_count = None
            for term in set(terms):
                pos = lowered.find(term)
                if pos == -1:
                    continue
                count = lowered.count(term)
                if best_count is None or count < best_count or (count == best_count and (best_pos is None or pos < best_pos)):
                    best_count = count
                    best_pos = pos
            hit_at = best_pos if best_pos is not None else -1

        if hit_at == -1:
            # Fallback: short head excerpt.
            return raw[:max_len].strip()

        # Window around the match: keep some lead-in context.
        lead = 220
        tail = max_len - lead
        start = max(0, hit_at - lead)
        end = min(len(raw), hit_at + max(120, tail))
        snippet = raw[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(raw):
            snippet = snippet + "..."
        return snippet

    def _recommendation_answer(self, bot_name: str, message: str) -> str:
        llm_client = self._get_llm_client()
        if llm_client is None:
            return "I can provide document-based answers. Please upload your documents and ask a document-specific question."

        system_prompt = (
            "You are a friendly advisor. Answer recommendation questions briefly and clearly. "
            "Do not reference documents because this is a general advice query."
        )
        user_prompt = f"Question: {message}\nAnswer in a short recommendation format."
        try:
            response = llm_client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=250,
                temperature=0.4,
                top_p=0.9,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or ""
            content = content.strip()
            if not content:
                raise RuntimeError("Empty LLM response")
            return content
        except Exception:
            # Fallback to a shorter conversational answer for recommendation.
            return self._direct_llm_answer(bot_name, message)

    def _direct_llm_answer(self, bot_name: str, message: str, *, history: list[ConversationEntry] | None = None) -> str:
        llm_client = self._get_llm_client()
        if llm_client is None:
            return "I could not access the LLM right now. Please try again later."

        system_prompt = (
            "You are a helpful assistant. Answer clearly and succinctly in markdown.\n"
            "- Do NOT bold entire sentences.\n"
            "- If you use bullets, use '-' and put each bullet on its own line."
        )
        history_block = self._history_block(history or [])
        user_prompt = f"{history_block}\n\nQuestion: {message}\nReturn markdown text only."
        try:
            response = llm_client.chat.completions.create(
                model=settings.llm_model,
                max_tokens=300,
                temperature=0.25,
                top_p=0.9,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = response.choices[0].message.content or ""
            content = content.strip()
            if not content:
                raise RuntimeError("Empty LLM response")
            return self._normalize_markdown_output(content)
        except Exception:
            return "I'm having trouble reaching the LLM right now. Please try again in a moment."

    @staticmethod
    def _normalize_markdown_output(text: str) -> str:
        """Normalize common LLM markdown glitches so the UI renders bullets/paragraphs correctly."""
        cleaned = (text or "").replace("\r\n", "\n").strip()
        if not cleaned:
            return cleaned

        # If the model wrapped the whole response in bold, unwrap it.
        if cleaned.startswith("**") and cleaned.endswith("**") and cleaned.count("**") <= 4:
            cleaned = cleaned.strip("*").strip()

        # Turn inline '*' bullet runs into real line bullets.
        # Example: "Key: * a * b" -> "Key:\n- a\n- b"
        cleaned = re.sub(r"(?m)^[ \t]*\\*[ \t]+", "- ", cleaned)  # leading '*' -> '-'
        cleaned = re.sub(r"\\s+\\*\\s+(?=\\S)", "\n- ", cleaned)  # inline " * item" -> newline bullet

        # Ensure bullets start on their own line.
        cleaned = re.sub(r"(?<!\\n)(-\\s+)", r"\n\\1", cleaned)

        # Collapse excessive blank lines.
        cleaned = re.sub(r"\\n{3,}", "\n\n", cleaned).strip()
        return cleaned

    @staticmethod
    def _history_block(history: list[ConversationEntry]) -> str:
        """Compact history block for prompts (kept short to avoid overpowering doc context)."""
        if not history:
            return ""

        tail = history[-6:]
        lines = ["Conversation so far (for reference):"]
        for entry in tail:
            role = "User" if entry.role == "user" else "Assistant"
            content = (entry.content or "").strip()
            if not content:
                continue
            content = ChatService._truncate_sentence_safe(content, 280)
            lines.append(f"{role}: {content}")
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    @staticmethod
    def _contextualize_query(history: list[ConversationEntry], message: str) -> str:
        """
        Build a retrieval-friendly query for short follow-ups like:
        "What about the grace period?" / "Does it apply to single premium policies?"
        """
        msg = (message or "").strip()
        if not msg or not history:
            return msg

        lowered = msg.lower()
        looks_like_followup = ChatService._is_followup_message(lowered)
        if not looks_like_followup:
            return msg

        last_user = ChatService._find_last_topic_user_message(history)

        # If the user explicitly asks to go deeper, drive retrieval using the last topic question
        # and avoid polluting the query with prior assistant output.
        if any(
            phrase in lowered
            for phrase in (
                "go deeper",
                "tell me more",
                "more detail",
                "expand on",
                "elaborate",
                "continue",
                "explain more",
                "more about it",
                "more about this",
            )
        ):
            # If the follow-up contains an explicit topic ("go deeper into physical access controls"),
            # use those keywords instead of forcing the previous topic.
            if ChatService._meaningful_token_count(msg) >= 2:
                return msg
            if last_user:
                return last_user
            return msg

        last_assistant = next((e.content for e in reversed(history) if e.role == "assistant" and (e.content or "").strip()), "")
        if not last_user:
            return msg

        contextual = f"{msg}\n\nPrevious user question: {ChatService._truncate_sentence_safe(last_user, 240)}"
        if last_assistant:
            contextual += f"\nPrevious assistant answer (reference only): {ChatService._truncate_sentence_safe(last_assistant, 200)}"
        return contextual

    @staticmethod
    def _is_followup_message(lowered: str) -> bool:
        # Follow-ups usually contain pronouns or explicit continuation phrasing.
        if re.search(r"\\b(it|that|this|they|those|them|there|these)\\b", lowered):
            return True
        if lowered.startswith(("and ", "also ", "what about", "then ", "so ", "does it", "is it", "are they")):
            return True
        if any(
            phrase in lowered
            for phrase in (
                "go deeper",
                "tell me more",
                "more detail",
                "expand on",
                "elaborate",
                "continue",
                "explain more",
                "more about it",
                "more about this",
            )
        ):
            return True
        return False

    @staticmethod
    def _find_last_topic_user_message(history: list[ConversationEntry]) -> str:
        # Skip follow-up-only user messages to avoid polluting context ("go deeper", etc.).
        for entry in reversed(history):
            if entry.role != "user":
                continue
            content = (entry.content or "").strip()
            if not content:
                continue
            if ChatService._is_followup_message(content.lower()):
                continue
            if ChatService._is_thin_query(content):
                continue
            return content
        return ""

    @staticmethod
    def _extract_section_number(message: str) -> str:
        m = re.search(r"\bsection\s+(\d{1,4})\b", (message or "").lower())
        if m:
            return m.group(1)
        return ""

    @staticmethod
    def _is_thin_query(message: str) -> bool:
        """
        A thin query is mostly references ("section 13", "this section") and lacks topical keywords.
        We use this to anchor retrieval to the last topic.
        """
        stop = {
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
            "section",
            "clause",
            "chapter",
            "appendix",
            "article",
            "paragraph",
            "para",
            "says",
            "say",
            "tell",
            "about",
        }
        tokens = [t for t in TOKEN_PATTERN.findall((message or "").lower()) if t]
        meaningful = [t for t in tokens if t not in stop and not t.isdigit() and len(t) >= 3]
        return len(meaningful) <= 1

    @staticmethod
    def _meaningful_token_count(message: str) -> int:
        stop = {
            "go",
            "deeper",
            "into",
            "this",
            "that",
            "it",
            "more",
            "about",
            "explain",
            "elaborate",
            "continue",
            "section",
            "clause",
            "chapter",
            "appendix",
            "article",
            "paragraph",
            "para",
            "please",
            "can",
            "you",
            "me",
            "tell",
            "say",
        }
        tokens = [t for t in TOKEN_PATTERN.findall((message or "").lower()) if t]
        meaningful = [t for t in tokens if t not in stop and not t.isdigit() and len(t) >= 3]
        return len(meaningful)

    def _is_cacheable(self, response: str, sources: list[SourceChunk]) -> bool:
        if not sources:
            return False
        if (
            "do not contain" in response.lower()
            or "could not find" in response.lower()
            or "information not found in document" in response.lower()
        ):
            return False
        return True

    @staticmethod
    def _format_structured_answer(title: str, key_points: list[str], details: list[str]) -> str:
        lines = ["## Answer", f"### {title}"]
        if key_points:
            lines.append("### Key Points")
            for pt in key_points:
                lines.append(f"- {pt}")
        if details:
            lines.append("### Details")
            for i, d in enumerate(details, start=1):
                lines.append(f"{i}. {d}")
        lines.append("### Summary")
        lines.append("This answer is based on uploaded documents.")
        return "\n".join(lines)


    @staticmethod
    def _get_llm_client():
        if OpenAI is None:
            return None
        if settings.llm_provider == "openai" and settings.openai_api_key:
            return OpenAI(api_key=settings.openai_api_key)
        if settings.llm_provider == "groq" and settings.groq_api_key:
            return OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
        return None

    @staticmethod
    def _definition_answer_if_available(message: str, source_list: list[SourceChunk]) -> str | None:
        normalized = message.lower()
        definition_markers = ("what is", "what does", "means", "mean", "define", "definition")
        if not any(marker in normalized for marker in definition_markers):
            return None

        term = ChatService._extract_definition_term(normalized)
        if not term:
            return None

        patterns = [
            rf"\b{re.escape(term)}\b\s+means\s+(.*?)(?:[.;]|$)",
            rf"\b{re.escape(term)}\b\s+refers to\s+(.*?)(?:[.;]|$)",
            rf"\b{re.escape(term)}\b\s+is\s+(.*?)(?:[.;]|$)",
        ]

        for source in source_list[: settings.max_context_chunks]:
            text = " ".join(source.excerpt.replace("\n", " ").split())
            lowered = text.lower()
            for pattern in patterns:
                match = re.search(pattern, lowered)
                if not match:
                    continue
                tail = match.group(1).strip(" .,:;")
                if not tail:
                    continue
                return f"'{term}' is defined as: {tail}."

        classified = ChatService._classification_from_context(term, source_list)
        if classified:
            return classified

        contextual = ChatService._contextual_meaning(term, source_list)
        if contextual:
            return (
                f"The documents do not explicitly define '{term}'. "
                f"Based on context: {contextual}"
            )

        return (
            f"I could not find an explicit definition of '{term}' in the uploaded documents. "
            "I can only answer based on what is explicitly written in your files."
        )

    @staticmethod
    def _extract_definition_term(normalized_message: str) -> str:
        patterns = [
            r"what does\s+(.+?)\s+mean",
            r"what is\s+(.+?)\s+mean",
            r"what is\s+(.+?)\??$",
            r"(.+?)\s+means\??$",
            r"define\s+(.+?)\??$",
            r"definition of\s+(.+?)\??$",
        ]
        for pattern in patterns:
            match = re.search(pattern, normalized_message.strip())
            if not match:
                continue
            term = match.group(1).strip(" ?.,:;\"'")
            if term:
                return term
        return ""

    @staticmethod
    def _contextual_meaning(term: str, source_list: list[SourceChunk]) -> str:
        term_tokens = [token for token in TOKEN_PATTERN.findall(term.lower()) if token]
        if not term_tokens:
            return ""

        candidates: list[tuple[int, str]] = []
        for source in source_list[: settings.max_context_chunks]:
            text = " ".join(source.excerpt.replace("\n", " ").split())
            units = re.split(r"(?<=[.!?])\s+|(?=\b\d+\s+[A-Z])", text)
            for unit in units:
                lowered = unit.lower()
                score = sum(1 for token in term_tokens if token in lowered)
                if score == 0:
                    continue
                # Prefer lines that actually explain/classify the term.
                if any(hint in lowered for hint in ("means", "refers to", "defined", "category", "type", "complaint")):
                    score += 2
                cleaned = ChatService._clean_unit(unit)
                if cleaned:
                    candidates.append((score, cleaned))

        if not candidates:
            return ""

        best = sorted(candidates, key=lambda item: (item[0], len(item[1])), reverse=True)[0][1]
        best = ChatService._normalize_contextual_line(best, term)
        if best.endswith("."):
            return best
        return best + "."

    @staticmethod
    def _classification_from_context(term: str, source_list: list[SourceChunk]) -> str:
        normalized_term = term.lower().strip()
        for source in source_list[: settings.max_context_chunks]:
            text = " ".join(source.excerpt.replace("\n", " ").split())
            lowered = text.lower()
            if normalized_term not in lowered:
                continue
            # Detect category/list context near the term.
            list_pattern = rf"(?:categorized into|category|types?)\s+([^.]*\b{re.escape(normalized_term)}\b[^.]*)"
            list_match = re.search(list_pattern, lowered)
            if list_match:
                return (
                    f"'{normalized_term}' appears as a complaint category in the uploaded policy, "
                    "not as a formally defined term."
                )
            # Detect direct list style: "product issues, service issues, ..."
            if re.search(rf"\b{re.escape(normalized_term)}\b\s*,", lowered):
                return (
                    f"'{normalized_term}' is listed as one complaint type in the policy, "
                    "but no formal definition is provided."
                )
        return ""

    @staticmethod
    def _steps_answer(message: str, source_list: list[SourceChunk]) -> str:
        sections = [source.excerpt for source in source_list[: settings.max_context_chunks]]
        joined = " ".join(sections)
        normalized = re.sub(r"\s+", " ", joined).strip()
        clauses = ChatService._extract_policy_clauses(normalized)
        if not clauses:
            return ""
        step_units = [
            clause
            for clause in clauses
            if any(term in clause.lower() for term in ("must", "initiate", "request", "submit", "review", "resolve", "escalate"))
        ]
        if not step_units:
            step_units = clauses
        selected = step_units[:4]
        title = "Steps"
        lowered = message.lower()
        if "complaint" in lowered:
            title = "Complaint handling steps"
        elif "return" in lowered:
            title = "Return request steps"
        lines = [f"{idx}. {ChatService._clean_unit(text)}" for idx, text in enumerate(selected, start=1)]
        return f"{title}:\n" + "\n".join(lines)

    @staticmethod
    def _policy_answer(message: str, source_list: list[SourceChunk]) -> str:
        query_terms = [token for token in TOKEN_PATTERN.findall(message.lower()) if len(token) > 2]
        clauses: list[tuple[int, str]] = []
        for source in source_list[: settings.max_context_chunks]:
            text = " ".join(source.excerpt.replace("\n", " ").split())
            for clause in ChatService._extract_policy_clauses(text):
                lowered = clause.lower()
                overlap = sum(1 for term in query_terms if term in lowered)
                if overlap > 0:
                    clauses.append((overlap, clause))
        if not clauses:
            return ""
        selected = [item[1] for item in sorted(clauses, key=lambda x: (x[0], len(x[1])), reverse=True)[:2]]
        summary = ". ".join(ChatService._clean_unit(text) for text in selected)
        if summary and not summary.endswith("."):
            summary += "."
        return summary

    @staticmethod
    def _normalize_contextual_line(text: str, term: str) -> str:
        cleaned = text
        # Remove policy-title prefaces that make answers look noisy.
        title_markers = [
            "Customer Complaint Management Policy",
            "E Commerce Customer Support Policy Sample Document",
            "E-Commerce Customer Support Policy (Sample Document)",
        ]
        for marker in title_markers:
            cleaned = cleaned.replace(marker, "").strip(" -:;,.")

        lowered = cleaned.lower()
        if "categorized as" in lowered or "category" in lowered or "type" in lowered:
            return (
                f"'{term}' appears as a complaint category in the uploaded policy, "
                "not as a formally defined term."
            )

        if len(cleaned) > 360:
            sentence_match = re.search(r"^(.{120,360}?[.!?])(?:\s|$)", cleaned)
            if sentence_match:
                cleaned = sentence_match.group(1).strip()
            else:
                cleaned = cleaned[:357].rstrip() + "..."
        return cleaned

    @staticmethod
    def _build_extractive_answer(bot_name: str, message: str, source_list: list[SourceChunk]) -> str:
        query_terms = [token for token in TOKEN_PATTERN.findall(message.lower()) if len(token) > 2]
        query_counter = Counter(query_terms)

        candidates: list[tuple[int, int, str]] = []
        seen = set()
        for source in source_list[:3]:
            normalized_source = " ".join(source.excerpt.replace("\n", " ").split())
            # PDFs often produce flat text; split by numbered section markers when sentence punctuation is weak.
            sections = re.split(r"(?=\b\d+\s+[A-Z][A-Za-z ]{2,40}\b)", normalized_source)
            if len(sections) <= 1:
                sections = re.split(r"(?<=[.!?])\s+", normalized_source)
            for section in sections:
                normalized = " ".join(section.split())
                if len(normalized) < 20:
                    continue
                lowered = normalized.lower()
                if lowered in seen:
                    continue
                seen.add(lowered)
                sent_counter = Counter(TOKEN_PATTERN.findall(lowered))
                overlap = sum(min(query_counter[t], sent_counter[t]) for t in query_counter) if query_counter else 0
                candidates.append((overlap, len(normalized), normalized))

        if candidates:
            ranked = sorted(candidates, key=lambda item: (item[0], item[1]), reverse=True)
            best_sections = [item[2] for item in ranked[:4]]
            if ranked[0][0] == 0:
                # Relevant docs found but weak keyword overlap: return a short, readable extract.
                lines = ["Answer:"]
                for idx, section in enumerate(best_sections[:3], start=1):
                    cleaned = ChatService._clean_unit(section, max_len=240)
                    if cleaned:
                        lines.append(f"- {cleaned}")
                if len(lines) == 1 and source_list:
                    lines.append(f"- {ChatService._clean_unit(source_list[0].excerpt, max_len=240)}")
                lines.append("- Source: extracted from your uploaded documents.")
                return "\n".join(lines).strip()
            output = ChatService._format_dynamic_fallback(message, best_sections)
            if len(output) < 120 and len(best_sections) > 1:
                extra = "\n\nMore from context:\n" + "\n".join(
                    ChatService._clean_unit(section, max_len=240) for section in best_sections[:2]
                )
                output = output.strip() + extra
            return output

        fallback = source_list[0].excerpt.strip()
        if fallback:
            fallback = re.sub(r"\s+", " ", fallback).strip()
            return fallback

        return (
            f"I could not find enough specific policy details for '{message}' in the indexed documents. "
            "Try a more specific question or upload more detailed documents."
        )

    @staticmethod
    def _normalize_json_answer(parsed: dict, bot_name: str) -> str:
        title = str(parsed.get("title") or f"{bot_name} answer")
        summary = str(parsed.get("summary") or parsed.get("answer") or "Answer extracted from documents.")

        sections = []
        if isinstance(parsed.get("sections"), list):
            for section in parsed.get("sections"):
                if isinstance(section, dict) and section.get("heading"):
                    points = section.get("points") if isinstance(section.get("points"), list) else []
                    sections.append({"heading": str(section.get("heading")), "points": [str(p) for p in points]})
        else:
            # fallback for older output keys
            bullets = parsed.get("key_points") or parsed.get("points") or parsed.get("bullet_points") or []
            if isinstance(bullets, list) and bullets:
                sections.append({"heading": "Key Points", "points": [str(x) for x in bullets]})
            details = parsed.get("details")
            if isinstance(details, list) and details:
                sections.append({"heading": "Details", "points": [str(x) for x in details]})

        if not sections:
            sections.append({"heading": "Answer", "points": [summary]})

        output = {
            "title": title,
            "sections": sections,
            "summary": summary,
        }
        return json.dumps(output, ensure_ascii=False)

    def _build_markdown_fallback(
        self,
        bot_name: str,
        message: str,
        source_list: list[SourceChunk],
        *,
        fallback_behavior: str = "strict",
        bot_description: str | None = None,
    ) -> str:
        fallback = ChatService._build_extractive_answer(bot_name, message, source_list)
        raw_lines = [line.strip("-* \t") for line in fallback.splitlines() if line.strip()]
        key_lines: list[str] = []
        source_line = ""
        for line in raw_lines:
            lowered = line.lower().strip()
            if lowered in ("answer:", "key points:", "context snippets:"):
                continue
            if lowered.startswith("source:"):
                source_line = line
                continue
            # Normalize numbered bullets like "1. ..."
            line = re.sub(r"^\d+\.\s+", "", line).strip()
            if line:
                key_lines.append(line)
        if not key_lines:
            return self._not_found_in_docs_answer(bot_name, fallback_behavior, bot_description)

        points = "\n".join(f"- {line}" for line in key_lines[:5])
        summary = key_lines[0]
        source_md = f"\n\n_{source_line}_" if source_line else ""
        return f"### {bot_name} answer\n\n{points}\n\nSummary: {summary}{source_md}"

    @staticmethod
    def _format_dynamic_fallback(message: str, sections: list[str]) -> str:
        query = message.lower()
        joined = " ".join(sections)
        normalized = re.sub(r"\s+", " ", joined).strip()
        units = ChatService._split_policy_units(normalized)
        clauses = ChatService._extract_policy_clauses(normalized)
        if not units:
            units = [normalized]

        response_lines: list[str] = []
        response_lines.append("Answer:")

        if any(keyword in query for keyword in ("step", "steps", "process", "how to", "procedure")):
            step_units = [
                unit
                for unit in (clauses if clauses else units)
                if any(term in unit.lower() for term in ("must", "initiate", "request", "return", "refund", "claim", "submit"))
            ]
            if not step_units:
                step_units = clauses if clauses else units
            response_lines.append("- Action Plan:")
            for i, unit in enumerate(step_units[:4], start=1):
                response_lines.append(f"  {i}. {ChatService._clean_unit(unit)}")
            response_lines.append("- Note: follow these steps in order and check policy clauses for exact conditions.")
            response_lines.append("- Source: extracted from uploaded document context.")
            return "\n".join(response_lines)

        if "deeper" in query or "go deeper" in query or "more detail" in query or "explain" in query:
            response_lines.append("- Detailed Context:")
            for i, unit in enumerate((clauses if clauses else units)[:4], start=1):
                response_lines.append(f"  {i}. {ChatService._clean_unit(unit)}")
            response_lines.append("- Summary:")
            response_lines.append(f"  - {ChatService._clean_unit((clauses if clauses else units)[0] if (clauses if clauses else units) else normalized)}")
            response_lines.append("- Reference: this is from your uploaded policy text.")
            return "\n".join(response_lines)

        relevant_pool = clauses if clauses else units
        policy_units = [unit for unit in relevant_pool if any(t in unit.lower() for t in ("return", "refund", "premium", "benefit", "claim", "nominee", "section 39", "policy bond"))]
        if policy_units:
            response_lines.append("- Key Points:")
            for i, unit in enumerate(policy_units[:4], start=1):
                summary = ChatService._clean_unit(unit)
                response_lines.append(f"  {i}. {summary}")
        else:
            response_lines.append("- Context Snippets:")
            for i, unit in enumerate(units[:3], start=1):
                summary = ChatService._clean_unit(unit)
                response_lines.append(f"  {i}. {summary}")

        response_lines.append("- Source: matched text from your uploaded documents.")
        return "\n".join(response_lines)

    @staticmethod
    def _split_policy_units(text: str) -> list[str]:
        parts = re.split(
            r"(?=\b(?:\d+\s+[A-Z][A-Za-z ]{2,40}|Products can|Customers must|Refund requests|Return Policy|Refund Policy|If the chatbot|Customer complaints)\b)",
            text,
        )
        units = [" ".join(part.split()) for part in parts if part and part.strip()]
        return units

    @staticmethod
    def _extract_policy_clauses(text: str) -> list[str]:
        starters = [
            "Products can",
            "Customers must",
            "Refund requests",
            "Customers can",
            "The support bot should",
            "If the chatbot cannot",
        ]
        starts = "|".join(re.escape(starter) for starter in starters)
        pattern = rf"((?:{starts}).*?)(?=(?:{starts})|\b\d+\s+[A-Z][A-Za-z ]{{2,40}}\b|$)"
        clauses = [re.sub(r"\s+", " ", match.strip()) for match in re.findall(pattern, text)]
        return [clause for clause in clauses if len(clause) > 25]

    @staticmethod
    def _truncate_sentence_safe(text: str, max_len: int | None) -> str:
        if max_len is None or len(text) <= max_len:
            return text.strip()
        # Prefer ending at natural punctuation or line break within max_len
        cut_off = max_len
        for sep in [". ", "! ", "? ", "; ", "\n"]:
            idx = text.rfind(sep, 0, max_len)
            if idx != -1:
                cut_off = idx + 1
                break
        truncated = text[:cut_off].rstrip()
        if len(truncated) >= len(text) or not truncated:
            truncated = text[:max_len]
        # avoid cutting in middle of word
        if not truncated.endswith(" ") and len(truncated) > 1 and truncated[-1].isalnum():
            last_space = truncated.rfind(" ")
            if last_space > 0:
                truncated = truncated[:last_space]
        if len(truncated) < len(text):
            truncated = truncated.rstrip(".,;:!?") + "..."
        return truncated.strip()

    @staticmethod
    def _clean_unit(text: str, max_len: int | None = None) -> str:
        cleaned = re.sub(r"^\d+\s+", "", text).strip()
        cleaned = re.sub(r"\s+", " ", cleaned)
        noise_markers = [
            "E Commerce Customer Support Policy Sample Document",
            "E-Commerce Customer Support Policy (Sample Document)",
            "Customer Complaint Management Policy",
        ]
        for marker in noise_markers:
            idx = cleaned.find(marker)
            if idx > 0:
                cleaned = cleaned[:idx].rstrip()
                break
        cleaned = cleaned.strip()
        # Improve readability for OCR/PDF artifacts.
        def _split_long_camel(match: re.Match[str]) -> str:
            token = match.group(0)
            return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", token)

        # Only split long CamelCase tokens (avoid breaking short brand names like "ChatDock").
        cleaned = re.sub(r"\b[A-Za-z]{18,}\b", _split_long_camel, cleaned)
        cleaned = re.sub(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])", " ", cleaned)  # 7days -> 7 days
        cleaned = re.sub(r"(?:\b\d+\b[\s,.;:/-]*){6,}", " ", cleaned)  # drop long numeric tables
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        # Fix common OCR-style tokenization like "Policyholder s" -> "Policyholder's"
        cleaned = re.sub(r"\b([A-Za-z]+)\s+s\b", r"\1's", cleaned)
        cleaned = re.sub(r"\bNominee\s+s\b", "Nominee's", cleaned)
        if max_len is not None and len(cleaned) > max_len:
            cleaned = ChatService._truncate_sentence_safe(cleaned, max_len)
        return cleaned

    @staticmethod
    def _cache_key(
        user_id: UUID,
        bot_id: UUID,
        normalized_query: str,
        section_ids: list[str] | None = None,
    ) -> str:
        section_part = hashlib.sha256(":".join(section_ids or []).encode("utf-8")).hexdigest()
        payload = f"{ChatService.CACHE_SCHEMA_VERSION}:{user_id}:{bot_id}:{normalized_query.strip().lower()}:{section_part}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _thread_title_from_message(message: str) -> str:
        normalized = " ".join((message or "").split()).strip()
        if not normalized:
            return "New chat"
        return normalized[:160]

    @staticmethod
    def _ensure_thread(user_id: UUID, bot_id: UUID, conversation_id: UUID, first_message: str) -> None:
        title = ChatService._thread_title_from_message(first_message)
        now = datetime.now(timezone.utc)
        if use_database():
            for db in get_db_session():
                record = db.get(ChatThreadORM, conversation_id)
                if record is None:
                    db.add(
                        ChatThreadORM(
                            id=conversation_id,
                            bot_id=bot_id,
                            user_id=user_id,
                            title=title,
                            created_at=now,
                            updated_at=now,
                        )
                    )
                else:
                    record.updated_at = now
                    if not record.title.strip() or record.title.strip().lower() == "new chat":
                        record.title = title
                db.commit()
                return

        existing = getattr(store, "chat_threads", {}).get(conversation_id)
        if existing is None:
            if not hasattr(store, "chat_threads"):
                store.chat_threads = {}
            store.chat_threads[conversation_id] = ChatThreadRecord(
                id=conversation_id,
                bot_id=bot_id,
                user_id=user_id,
                title=title,
                created_at=now,
                updated_at=now,
            )
        else:
            existing.updated_at = now
            if not existing.title.strip() or existing.title.strip().lower() == "new chat":
                existing.title = title

    @staticmethod
    def _load_thread_history(user_id: UUID, bot_id: UUID, conversation_id: UUID) -> list[ConversationEntry]:
        entries: list[ConversationEntry] = []
        if use_database():
            for db in get_db_session():
                logs = (
                    db.execute(
                        select(ChatLogORM)
                        .where(
                            ChatLogORM.user_id == user_id,
                            ChatLogORM.bot_id == bot_id,
                            ChatLogORM.conversation_id == conversation_id,
                        )
                        .order_by(ChatLogORM.timestamp.asc())
                    )
                    .scalars()
                    .all()
                )
                for log in logs:
                    created_at = log.timestamp.isoformat()
                    entries.append(ConversationEntry(role="user", content=log.question, created_at=created_at))
                    entries.append(ConversationEntry(role="assistant", content=log.response, created_at=created_at))
                return entries

        logs = [
            log
            for log in store.chat_logs.values()
            if log.user_id == user_id and log.bot_id == bot_id and getattr(log, "conversation_id", None) == conversation_id
        ]
        logs.sort(key=lambda log: log.timestamp)
        for log in logs:
            created_at = log.timestamp.isoformat()
            entries.append(ConversationEntry(role="user", content=log.question, created_at=created_at))
            entries.append(ConversationEntry(role="assistant", content=log.response, created_at=created_at))
        return entries

    @staticmethod
    def _log_query(user_id: UUID, bot_id: UUID, conversation_id: UUID, message: str, response: str, cached: bool) -> None:
        if use_database():
            for db in get_db_session():
                thread = db.get(ChatThreadORM, conversation_id)
                if thread is None:
                    now = datetime.now(timezone.utc)
                    thread = ChatThreadORM(
                        id=conversation_id,
                        bot_id=bot_id,
                        user_id=user_id,
                        title=ChatService._thread_title_from_message(message),
                        created_at=now,
                        updated_at=now,
                    )
                    db.add(thread)
                else:
                    thread.updated_at = datetime.now(timezone.utc)
                    if not thread.title.strip() or thread.title.strip().lower() == "new chat":
                        thread.title = ChatService._thread_title_from_message(message)
                db.add(
                    ChatLogORM(
                        id=store.next_id(),
                        conversation_id=conversation_id,
                        bot_id=bot_id,
                        user_id=user_id,
                        question=message,
                        response=response,
                        cached=cached,
                        timestamp=datetime.now(timezone.utc),
                    )
                )
                db.commit()
                return

        record = ChatLogRecord(
            id=store.next_id(),
            conversation_id=conversation_id,
            bot_id=bot_id,
            user_id=user_id,
            question=message,
            response=response,
            cached=cached,
            timestamp=datetime.now(timezone.utc),
        )
        thread = store.chat_threads.get(conversation_id)
        if thread is not None:
            thread.updated_at = record.timestamp
            if not thread.title.strip() or thread.title.strip().lower() == "new chat":
                thread.title = ChatService._thread_title_from_message(message)
        store.chat_logs[record.id] = record

    @staticmethod
    def _get_bot_for_user(user_id: UUID, bot_id: UUID) -> BotRecord:
        if use_database():
            for db in get_db_session():
                record = db.get(BotORM, bot_id)
                if record is None or record.user_id != user_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
                return BotRecord(
                    id=record.id,
                    user_id=record.user_id,
                    bot_name=record.bot_name,
                    description=record.description,
                    created_at=record.created_at,
                    archived=record.archived,
                    tone=record.tone,
                    answer_length=record.answer_length,
                    fallback_behavior=record.fallback_behavior,
                    system_prompt=record.system_prompt,
                    greeting_message=record.greeting_message,
                    updated_at=record.updated_at,
                )

        bot = store.bots.get(bot_id)
        if bot is None or bot.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
        return bot

    @staticmethod
    def _bot_has_documents(bot_id: UUID) -> bool:
        if use_database():
            for db in get_db_session():
                count = db.execute(
                    select(func.count()).select_from(DocumentORM).where(DocumentORM.bot_id == bot_id)
                ).scalar_one()
                return int(count) > 0
        return any(document.bot_id == bot_id for document in store.documents.values())

    @staticmethod
    def _get_document(document_id: UUID):
        if use_database():
            for db in get_db_session():
                return db.get(DocumentORM, document_id)
        return store.documents.get(document_id)

    @staticmethod
    def analytics_overview(user_id: UUID, bot_id: UUID | None = None) -> AnalyticsOverview:
        def compute_trend_and_top_and_bot_stats(logs: list[ChatLogORM], bot_name_by_id: dict[str, str]) -> tuple[list[int], list[TopQuery], list[BotQueryStat]]:
            trend = [0] * 7
            top = Counter()
            bot_counts = Counter()
            today_utc = datetime.now(timezone.utc).date()
            for log in logs:
                query_date = log.timestamp.date()
                day_index = (today_utc - query_date).days
                if 0 <= day_index < 7:
                    trend[6 - day_index] += 1
                top[log.question.strip()] += 1
                bot_counts[log.bot_id] += 1
            top_queries = [TopQuery(question=q, count=c) for q, c in top.most_common(5)]
            bot_queries = [BotQueryStat(bot_id=bot_id, bot_name=bot_name_by_id.get(bot_id, "Unknown Bot"), queries=count) for bot_id, count in bot_counts.most_common(5)]
            return trend, top_queries, bot_queries

        from app.services.bot_service import bot_service

        selected_bot = bot_service.get_owned(user_id, bot_id) if bot_id is not None else None

        if use_database():
            for db in get_db_session():
                total_bots = int(
                    db.execute(select(func.count()).select_from(BotORM).where(BotORM.user_id == user_id)).scalar_one()
                )
                owned_bots_query = select(BotORM.id, BotORM.bot_name).where(BotORM.user_id == user_id)
                if selected_bot is not None:
                    owned_bots_query = owned_bots_query.where(BotORM.id == selected_bot.id)
                owned_bots = db.execute(owned_bots_query).all()
                owned_bot_ids = [row[0] for row in owned_bots]
                bot_name_by_id = {row[0]: row[1] for row in owned_bots}

                if owned_bot_ids:
                    total_documents = int(
                        db.execute(
                            select(func.count()).select_from(DocumentORM).where(DocumentORM.bot_id.in_(owned_bot_ids))
                        ).scalar_one()
                    )
                    total_chunks = int(
                        db.execute(select(func.count()).select_from(ChunkORM).where(ChunkORM.bot_id.in_(owned_bot_ids))).scalar_one()
                    )
                else:
                    total_documents = 0
                    total_chunks = 0

                logs_query = select(ChatLogORM).where(ChatLogORM.user_id == user_id)
                if selected_bot is not None:
                    logs_query = logs_query.where(ChatLogORM.bot_id == selected_bot.id)
                logs = db.execute(logs_query).scalars().all()
                total_queries = len(logs)
                cached_queries = sum(1 for log in logs if log.cached)
                query_trend_last_7_days, top_queries, bot_queries = compute_trend_and_top_and_bot_stats(logs, bot_name_by_id)
                return AnalyticsOverview(
                    user_id=user_id,
                    selected_bot_id=selected_bot.id if selected_bot is not None else None,
                    selected_bot_name=selected_bot.bot_name if selected_bot is not None else None,
                    total_bots=total_bots,
                    total_documents=total_documents,
                    total_chunks=total_chunks,
                    total_queries=total_queries,
                    cached_queries=cached_queries,
                    query_trend_last_7_days=query_trend_last_7_days,
                    top_queries=top_queries,
                    bot_queries=bot_queries,
                )

        owned_bot_records = bot_service.list_for_user(user_id)
        owned_bots = {bot.id for bot in owned_bot_records}
        if selected_bot is not None:
            owned_bots = {selected_bot.id}
        total_documents = sum(1 for document in store.documents.values() if document.bot_id in owned_bots)
        total_chunks = sum(1 for chunk in store.chunks.values() if chunk.bot_id in owned_bots)
        logs = [
            log
            for log in store.chat_logs.values()
            if log.user_id == user_id and (selected_bot is None or log.bot_id == selected_bot.id)
        ]

        # Build names for fallback bots from store
        bot_name_by_id = {
            bot.id: bot.bot_name
            for bot in owned_bot_records
            if selected_bot is None or bot.id == selected_bot.id
        }
        query_trend_last_7_days, top_queries, bot_queries = compute_trend_and_top_and_bot_stats(logs, bot_name_by_id)

        return AnalyticsOverview(
            user_id=user_id,
            selected_bot_id=selected_bot.id if selected_bot is not None else None,
            selected_bot_name=selected_bot.bot_name if selected_bot is not None else None,
            total_bots=len(owned_bots),
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_queries=len(logs),
            cached_queries=sum(1 for log in logs if log.cached),
            query_trend_last_7_days=query_trend_last_7_days,
            top_queries=top_queries,
            bot_queries=bot_queries,
        )

    @staticmethod
    def list_threads(user_id: UUID, bot_id: UUID) -> list[ChatThreadSummary]:
        if use_database():
            for db in get_db_session():
                threads = (
                    db.execute(
                        select(ChatThreadORM)
                        .where(ChatThreadORM.user_id == user_id, ChatThreadORM.bot_id == bot_id)
                        .order_by(ChatThreadORM.updated_at.desc())
                    )
                    .scalars()
                    .all()
                )
                logs = (
                    db.execute(
                        select(ChatLogORM)
                        .where(ChatLogORM.user_id == user_id, ChatLogORM.bot_id == bot_id)
                        .order_by(ChatLogORM.timestamp.asc())
                    )
                    .scalars()
                    .all()
                )
                log_map: dict[UUID, list[ChatLogORM]] = defaultdict(list)
                for log in logs:
                    log_map[log.conversation_id].append(log)
                return [ChatService._thread_summary_from_db(thread, log_map.get(thread.id, [])) for thread in threads]

        threads = [
            thread
            for thread in store.chat_threads.values()
            if thread.user_id == user_id and thread.bot_id == bot_id
        ]
        threads.sort(key=lambda thread: thread.updated_at, reverse=True)
        logs = [
            log
            for log in store.chat_logs.values()
            if log.user_id == user_id and log.bot_id == bot_id
        ]
        log_map: dict[UUID, list[ChatLogRecord]] = defaultdict(list)
        for log in logs:
            log_map[log.conversation_id].append(log)
        return [ChatService._thread_summary_from_memory(thread, log_map.get(thread.id, [])) for thread in threads]

    @staticmethod
    def create_thread(user_id: UUID, bot_id: UUID, title: str | None = None) -> ChatThreadSummary:
        thread_id = uuid4()
        now = datetime.now(timezone.utc)
        thread_title = (title or "New chat").strip() or "New chat"
        if use_database():
            for db in get_db_session():
                record = ChatThreadORM(
                    id=thread_id,
                    bot_id=bot_id,
                    user_id=user_id,
                    title=thread_title[:160],
                    created_at=now,
                    updated_at=now,
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                return ChatService._thread_summary_from_db(record, [])

        record = ChatThreadRecord(
            id=thread_id,
            bot_id=bot_id,
            user_id=user_id,
            title=thread_title[:160],
            created_at=now,
            updated_at=now,
        )
        store.chat_threads[thread_id] = record
        return ChatService._thread_summary_from_memory(record, [])

    @staticmethod
    def rename_thread(user_id: UUID, bot_id: UUID, thread_id: UUID, title: str) -> ChatThreadSummary:
        cleaned_title = title.strip()[:160] or "New chat"
        if use_database():
            for db in get_db_session():
                thread = db.get(ChatThreadORM, thread_id)
                if thread is None or thread.user_id != user_id or thread.bot_id != bot_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")
                thread.title = cleaned_title
                thread.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(thread)
                logs = (
                    db.execute(
                        select(ChatLogORM)
                        .where(ChatLogORM.conversation_id == thread_id)
                        .order_by(ChatLogORM.timestamp.asc())
                    )
                    .scalars()
                    .all()
                )
                return ChatService._thread_summary_from_db(thread, logs)

        thread = store.chat_threads.get(thread_id)
        if thread is None or thread.user_id != user_id or thread.bot_id != bot_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")
        thread.title = cleaned_title
        thread.updated_at = datetime.now(timezone.utc)
        logs = [log for log in store.chat_logs.values() if log.conversation_id == thread_id]
        logs.sort(key=lambda log: log.timestamp)
        return ChatService._thread_summary_from_memory(thread, logs)

    @staticmethod
    def delete_thread(user_id: UUID, bot_id: UUID, thread_id: UUID) -> None:
        if use_database():
            for db in get_db_session():
                thread = db.get(ChatThreadORM, thread_id)
                if thread is None or thread.user_id != user_id or thread.bot_id != bot_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")
                db.execute(delete(ChatLogORM).where(ChatLogORM.conversation_id == thread_id))
                db.delete(thread)
                db.commit()
                return

        thread = store.chat_threads.get(thread_id)
        if thread is None or thread.user_id != user_id or thread.bot_id != bot_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat thread not found")
        store.chat_threads.pop(thread_id, None)
        log_ids = [log_id for log_id, log in store.chat_logs.items() if log.conversation_id == thread_id]
        for log_id in log_ids:
            store.chat_logs.pop(log_id, None)

    @staticmethod
    def _thread_summary_from_db(thread: ChatThreadORM, logs: list[ChatLogORM]) -> ChatThreadSummary:
        messages: list[ChatThreadMessage] = []
        for log in logs:
            messages.append(ChatThreadMessage(role="user", text=log.question, created_at=log.timestamp.isoformat()))
            messages.append(ChatThreadMessage(role="assistant", text=log.response, created_at=log.timestamp.isoformat()))
        return ChatThreadSummary(
            id=thread.id,
            bot_id=thread.bot_id,
            title=thread.title,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            messages=messages,
            logs=[],
        )

    @staticmethod
    def _thread_summary_from_memory(thread: ChatThreadRecord, logs: list[ChatLogRecord]) -> ChatThreadSummary:
        messages: list[ChatThreadMessage] = []
        for log in logs:
            messages.append(ChatThreadMessage(role="user", text=log.question, created_at=log.timestamp.isoformat()))
            messages.append(ChatThreadMessage(role="assistant", text=log.response, created_at=log.timestamp.isoformat()))
        return ChatThreadSummary(
            id=thread.id,
            bot_id=thread.bot_id,
            title=thread.title,
            created_at=thread.created_at.isoformat(),
            updated_at=thread.updated_at.isoformat(),
            messages=messages,
            logs=[],
        )


chat_service = ChatService()


def retrieve_sections_only(query: str) -> list[str]:
    """
    Return selected section headings BEFORE LLM.
    Example:
    ["logical access controls", "physical access controls"]
    """
    bot_id = _latest_bot_with_documents()
    if bot_id is None:
        return []
    sources, _normalized_query = chat_service._search(bot_id=bot_id, message=query, logs=[])
    sections: list[str] = []
    for source in sources:
        heading = extract_chunk_metadata(source.excerpt).get("normalized_heading", "").strip().lower()
        if heading and heading not in sections:
            sections.append(heading)
    return sections


def _latest_bot_with_documents() -> UUID | None:
    if use_database():
        for db in get_db_session():
            row = (
                db.execute(
                    select(BotORM.id)
                    .join(DocumentORM, DocumentORM.bot_id == BotORM.id)
                    .group_by(BotORM.id, BotORM.created_at)
                    .order_by(BotORM.created_at.desc())
                )
                .scalars()
                .first()
            )
            return row
        return None

    bot_ids_with_docs = {document.bot_id for document in store.documents.values()}
    if not bot_ids_with_docs:
        return None
    candidates = [bot for bot in store.bots.values() if bot.id in bot_ids_with_docs]
    if not candidates:
        return None
    candidates.sort(key=lambda bot: bot.created_at, reverse=True)
    return candidates[0].id
