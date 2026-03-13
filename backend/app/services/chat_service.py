from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from collections import Counter
from typing import Iterable, Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.core.cache import cache_service
from app.core.config import settings
from app.database.connection import get_db_session, use_database, store
from app.database.models import BotORM, ChatLogORM, ChunkORM, DocumentORM
from app.models.chat_model import ChatLogRecord
from app.rag.vector_store import get_chunk_by_id, vector_store
from app.rag.chunking import TOKEN_PATTERN
from app.schemas.chat_schema import AnalyticsOverview, SourceChunk

try:
    from openai import OpenAI  # type: ignore
except ImportError:  # pragma: no cover
    OpenAI = None


class ChatService:
    CACHE_SCHEMA_VERSION = "v14"

    def answer(self, user_id: UUID, bot_id: UUID, message: str) -> tuple[str, bool, list[SourceChunk]]:
        bot_name = self._get_bot_name_for_user(user_id, bot_id)

        cache_key = self._cache_key(user_id, bot_id, message)
        cached_response = cache_service.get(cache_key)
        sources = self._search(bot_id, message)
        if cached_response is not None:
            self._log_query(user_id, bot_id, message, cached_response, cached=True)
            return cached_response, True, sources

        response = self._generate_answer(bot_name, message, sources)
        cache_service.set(cache_key, response)
        self._log_query(user_id, bot_id, message, response, cached=False)
        return response, False, sources

    def _search(self, bot_id: UUID, message: str) -> list[SourceChunk]:
        hits = vector_store.search(bot_id=bot_id, query=message, limit=settings.max_context_chunks)
        if not hits:
            return []

        sources: list[SourceChunk] = []
        for hit in hits:
            chunk = get_chunk_by_id(hit.chunk_id)
            if chunk is None:
                continue
            document = self._get_document(chunk.document_id)
            if document is None:
                continue
            sources.append(
                SourceChunk(
                    document_id=chunk.document_id,
                    document_name=document.file_name,
                    chunk_id=chunk.id,
                    score=round(hit.score, 3),
                    excerpt=chunk.text[:2_000],
                )
            )
        return sources

    def _generate_answer(self, bot_name: str, message: str, sources: Iterable[SourceChunk]) -> str:
        source_list = list(sources)
        if not source_list:
            return (
                f"{bot_name} could not find supporting context for: '{message}'. "
                "Upload more documents or ask a narrower question."
            )

        intent = self._detect_intent(message)
        if intent == "definition":
            definition = self._definition_answer_if_available(message, source_list)
            if definition is not None:
                return definition
        if intent == "steps":
            steps = self._steps_answer(message, source_list)
            if steps:
                return steps
            return "I could not find explicit step-by-step instructions for this request in the uploaded documents."
        if intent == "policy":
            policy = self._policy_answer(message, source_list)
            if policy:
                return policy

        llm_client = self._get_llm_client()
        if llm_client is not None:
            try:
                context = "\n".join(f"- {source.excerpt}" for source in source_list[: settings.max_context_chunks])
                prompt = (
                    f"You are {bot_name}. Answer the user question using only the context.\n"
                    f"Context:\n{context}\n\nQuestion: {message}"
                )
                response = llm_client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Return a clean direct answer in 2-4 short sentences. "
                                "Do not repeat the question. Do not add filler. "
                                "Use only facts present in the provided context. "
                                "If detail is missing, clearly say it is not found in context. "
                                "Do not infer or define terms that are not explicitly defined."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                if content:
                    return content.strip()
            except Exception:
                pass

        return self._build_extractive_answer(bot_name, message, source_list)

    @staticmethod
    def _detect_intent(message: str) -> Literal["definition", "steps", "policy", "general"]:
        normalized = message.lower().strip()
        if any(marker in normalized for marker in ("what is", "what does", "means", "mean", "define", "definition")):
            return "definition"
        if any(marker in normalized for marker in ("step", "steps", "process", "procedure", "how should")):
            return "steps"
        if any(marker in normalized for marker in ("policy", "rule", "guideline", "handle", "handled")):
            return "policy"
        return "general"

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
                cleaned = ChatService._clean_unit(unit, max_len=420)
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
        lines = [f"{idx}. {ChatService._clean_unit(text, max_len=190)}" for idx, text in enumerate(selected, start=1)]
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
        summary = ". ".join(ChatService._clean_unit(text, max_len=220) for text in selected)
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
            if ranked[0][0] == 0:
                return (
                    f"I could not find a specific answer for '{message}' in the indexed documents. "
                    "Please upload a document with explicit policy details for this topic."
                )
            best_sections = [item[2] for item in ranked[:3]]
            return ChatService._format_dynamic_fallback(message, best_sections)

        fallback = source_list[0].excerpt.strip()
        if fallback:
            fallback = re.sub(r"\s+", " ", fallback).strip()
            if len(fallback) > 280:
                fallback = fallback[:277].rstrip() + "..."
            return fallback

        return (
            f"I could not find enough specific policy details for '{message}' in the indexed documents. "
            "Try a more specific question or upload more detailed documents."
        )

    @staticmethod
    def _format_dynamic_fallback(message: str, sections: list[str]) -> str:
        query = message.lower()
        joined = " ".join(sections)
        normalized = re.sub(r"\s+", " ", joined).strip()
        units = ChatService._split_policy_units(normalized)
        clauses = ChatService._extract_policy_clauses(normalized)
        if not units:
            units = [normalized]

        if any(keyword in query for keyword in ("step", "steps", "process", "how to", "procedure")):
            step_units = [
                unit
                for unit in (clauses if clauses else units)
                if any(term in unit.lower() for term in ("must", "initiate", "request", "return", "refund"))
            ]
            if not step_units:
                step_units = clauses if clauses else units
            selected = step_units[:3]
            lines = [f"{index}. {ChatService._clean_unit(unit, max_len=200)}" for index, unit in enumerate(selected, start=1)]
            return "Steps for return request:\n" + "\n".join(lines)

        relevant_pool = clauses if clauses else units
        policy_units = [unit for unit in relevant_pool if any(t in unit.lower() for t in ("return", "refund"))]
        picked = policy_units[:2] if policy_units else relevant_pool[:1]
        top = ". ".join(ChatService._clean_unit(unit, max_len=320) for unit in picked if ChatService._clean_unit(unit))
        if len(top) > 320:
            top = top[:317].rstrip() + "..."
        return top

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
    def _clean_unit(text: str, max_len: int = 320) -> str:
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
        if len(cleaned) > max_len:
            cleaned = cleaned[: max_len - 3].rstrip() + "..."
        return cleaned

    @staticmethod
    def _cache_key(user_id: UUID, bot_id: UUID, message: str) -> str:
        payload = f"{ChatService.CACHE_SCHEMA_VERSION}:{user_id}:{bot_id}:{message.strip().lower()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _log_query(user_id: UUID, bot_id: UUID, message: str, response: str, cached: bool) -> None:
        if use_database():
            for db in get_db_session():
                db.add(
                    ChatLogORM(
                        id=store.next_id(),
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
            bot_id=bot_id,
            user_id=user_id,
            question=message,
            response=response,
            cached=cached,
            timestamp=datetime.now(timezone.utc),
        )
        store.chat_logs[record.id] = record

    @staticmethod
    def _get_bot_name_for_user(user_id: UUID, bot_id: UUID) -> str:
        if use_database():
            for db in get_db_session():
                bot = db.get(BotORM, bot_id)
                if bot is None or bot.user_id != user_id:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
                return bot.bot_name

        bot = store.bots.get(bot_id)
        if bot is None or bot.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")
        return bot.bot_name

    @staticmethod
    def _get_document(document_id: UUID):
        if use_database():
            for db in get_db_session():
                return db.get(DocumentORM, document_id)
        return store.documents.get(document_id)

    @staticmethod
    def analytics_overview(user_id: UUID) -> AnalyticsOverview:
        if use_database():
            for db in get_db_session():
                total_bots = int(
                    db.execute(select(func.count()).select_from(BotORM).where(BotORM.user_id == user_id)).scalar_one()
                )
                owned_bot_ids = [row[0] for row in db.execute(select(BotORM.id).where(BotORM.user_id == user_id)).all()]
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
                total_queries = int(
                    db.execute(select(func.count()).select_from(ChatLogORM).where(ChatLogORM.user_id == user_id)).scalar_one()
                )
                cached_queries = int(
                    db.execute(
                        select(func.count()).select_from(ChatLogORM).where(ChatLogORM.user_id == user_id, ChatLogORM.cached.is_(True))
                    ).scalar_one()
                )
                return AnalyticsOverview(
                    user_id=user_id,
                    total_bots=total_bots,
                    total_documents=total_documents,
                    total_chunks=total_chunks,
                    total_queries=total_queries,
                    cached_queries=cached_queries,
                )

        from app.services.bot_service import bot_service

        owned_bots = {bot.id for bot in bot_service.list_for_user(user_id)}
        total_documents = sum(1 for document in store.documents.values() if document.bot_id in owned_bots)
        total_chunks = sum(1 for chunk in store.chunks.values() if chunk.bot_id in owned_bots)
        logs = [log for log in store.chat_logs.values() if log.user_id == user_id]
        return AnalyticsOverview(
            user_id=user_id,
            total_bots=len(owned_bots),
            total_documents=total_documents,
            total_chunks=total_chunks,
            total_queries=len(logs),
            cached_queries=sum(1 for log in logs if log.cached),
        )


chat_service = ChatService()
