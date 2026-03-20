from __future__ import annotations

import unittest
from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

from app.rag.hybrid_ranker import merge_and_rerank
from app.rag.keyword_search import keyword_search
from app.rag.document_processor import extract_chunk_metadata
from app.rag.query_rewriter import detect_query_type, rewrite_query
from app.services.chat_service import ChatService


@dataclass
class FakeChunk:
    id: object
    text: str


EVALUATION_SET = [
    {"query": "Development Methodology", "expected_heading": "development methodology"},
    {"query": "Logical Access Controls", "expected_heading": "logical access controls"},
    {"query": "Explain Service Level Management", "expected_heading": "service level management"},
]


class HybridRetrievalEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.chunks = [
            FakeChunk(
                id=uuid4(),
                text=(
                    "Title: Development Methodology\n"
                    "Heading: Development Methodology\n"
                    "NormalizedHeading: development methodology\n"
                    "Topic: development_methodology\n"
                    "Type: policy_section\n\n"
                    "Development projects follow formal practices, documentation, review checkpoints, and testing procedures."
                ),
            ),
            FakeChunk(
                id=uuid4(),
                text=(
                    "Title: Logical Access Controls\n"
                    "Heading: Logical Access Controls\n"
                    "NormalizedHeading: logical access controls\n"
                    "Topic: logical_access_controls\n"
                    "Type: policy_section\n\n"
                    "No user may access systems without authorization. User IDs must remain unique and not be shared."
                ),
            ),
            FakeChunk(
                id=uuid4(),
                text=(
                    "Title: Service Level Management\n"
                    "Heading: Service Level Management\n"
                    "NormalizedHeading: service level management\n"
                    "Topic: service_level_management\n"
                    "Type: policy_section\n\n"
                    "Service level targets are agreed with users and reviewed through periodic reporting and SLA analysis."
                ),
            ),
        ]
        self.chunk_by_id = {chunk.id: chunk for chunk in self.chunks}

    def test_query_rewriter_detects_lookup_and_explain(self) -> None:
        self.assertEqual(detect_query_type("Development Methodology"), "lookup")
        self.assertEqual(detect_query_type("Explain Service Level Management"), "explain")
        self.assertIn("process", rewrite_query("Development Methodology").lower())

    def test_evaluation_set_hits_expected_heading(self) -> None:
        successes = 0
        for item in EVALUATION_SET:
            keyword_hits = keyword_search(item["query"], self.chunks, limit=20)
            vector_hits = [
                SimpleNamespace(chunk_id=chunk.id, score=0.82 if item["expected_heading"] in chunk.text.lower() else 0.08)
                for chunk in self.chunks
            ]
            ranked = merge_and_rerank(item["query"], vector_hits, keyword_hits, self.chunk_by_id.get)
            self.assertTrue(ranked)
            top_heading = ranked[0]["normalized_heading"]
            if item["expected_heading"] == top_heading:
                successes += 1

        retrieval_success_rate = successes / len(EVALUATION_SET)
        self.assertGreaterEqual(retrieval_success_rate, 1.0)

    def test_heading_first_search_finds_logical_access_controls(self) -> None:
        matches = ChatService._heading_search("logical access controls", self.chunks, [])
        self.assertTrue(matches)
        top_chunk, _score = matches[0]
        self.assertIn("Logical Access Controls", top_chunk.text)

    def test_section_ids_exist_for_grouping(self) -> None:
        metadata = extract_chunk_metadata(self.chunks[0].text)
        self.assertTrue(metadata["section_id"])


if __name__ == "__main__":
    unittest.main()
