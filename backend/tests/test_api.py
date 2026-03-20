import io
import os
import sys
import unittest
from uuid import uuid4

from starlette.datastructures import UploadFile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.cache import cache_service
from app.core.rate_limiter import rate_limiter
from app.database.connection import store
from app.rag.query_rewriter import rewrite_query
from app.services.auth_service import auth_service
from app.services.bot_service import bot_service
from app.services.chat_service import ChatService, chat_service
from app.services.document_service import document_service


class ChatDockServiceTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        store.reset()
        cache_service.clear()
        rate_limiter.reset()

    async def test_end_to_end_txt_ingestion_and_cached_chat(self) -> None:
        user, token = auth_service.register("founder@example.com", "supersecure123")
        self.assertTrue(token)

        bot = bot_service.create(
            user.id,
            "Sales Copilot",
            "Handles product FAQs",
        )
        upload = UploadFile(
            file=io.BytesIO(b"ChatDock has fast answers, analytics, and embeddable widgets."),
            filename="pricing.txt",
            headers={"content-type": "text/plain"},
        )
        document, chunks = await document_service.ingest(bot.id, upload)
        self.assertEqual(document.file_name, "pricing.txt")
        self.assertGreaterEqual(len(chunks), 1)

        answer, cached, sources, _logs, conv_id = chat_service.answer(
            user.id,
            bot.id,
            "What does ChatDock provide?",
        )
        self.assertFalse(cached)
        self.assertTrue(conv_id)
        self.assertGreaterEqual(len(sources), 1)
        self.assertIn("ChatDock", answer)

        _, cached_again, _, _logs2, conv_id2 = chat_service.answer(
            user.id,
            bot.id,
            "What does ChatDock provide?",
            conversation_id=conv_id,
        )
        self.assertTrue(cached_again)
        self.assertEqual(conv_id, conv_id2)
        logs = list(store.chat_logs.values())
        self.assertEqual(len(logs), 2)
        self.assertEqual(sum(1 for log in logs if log.cached), 1)

    async def test_intent_detection_does_not_false_match_hi_in_this(self) -> None:
        # Regression test: "hi" was previously matched as a substring inside "this".
        from app.services.chat_service import ChatService

        self.assertEqual(ChatService._detect_intent("HDFC Life Pragati go deeper into this"), "document")

    async def test_document_name_query_is_answered_without_retrieval(self) -> None:
        user, token = auth_service.register("docs@example.com", "supersecure123")
        bot = bot_service.create(user.id, "Doc Bot", "Test bot")
        upload = UploadFile(
            file=io.BytesIO(b"Hello world"),
            filename="hello.txt",
            headers={"content-type": "text/plain"},
        )
        await document_service.ingest(bot.id, upload)
        answer, _cached, _sources, _logs, _conv = chat_service.answer(user.id, bot.id, "List the uploaded document names.")
        self.assertIn("Uploaded documents", answer)
        self.assertIn("hello.txt", answer)

    async def test_short_query_is_rewritten_for_retrieval(self) -> None:
        rewritten = rewrite_query("Development Methodology")
        self.assertIn("Development Methodology", rewritten)
        self.assertIn("document", rewritten.lower())

    async def test_cache_key_changes_with_chunk_ids(self) -> None:
        user_id = uuid4()
        bot_id = uuid4()
        key_one = ChatService._cache_key(user_id, bot_id, "Development Methodology", ["a", "b"])
        key_two = ChatService._cache_key(user_id, bot_id, "Development Methodology", ["a", "c"])
        self.assertNotEqual(key_one, key_two)


if __name__ == "__main__":
    unittest.main()
