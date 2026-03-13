import io
import os
import sys
import unittest

from starlette.datastructures import UploadFile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.cache import cache_service
from app.core.rate_limiter import rate_limiter
from app.database.connection import store
from app.services.auth_service import auth_service
from app.services.bot_service import bot_service
from app.services.chat_service import chat_service
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

        answer, cached, sources = chat_service.answer(
            user.id,
            bot.id,
            "What does ChatDock provide?",
        )
        self.assertFalse(cached)
        self.assertGreaterEqual(len(sources), 1)
        self.assertIn("ChatDock", answer)

        _, cached_again, _ = chat_service.answer(
            user.id,
            bot.id,
            "What does ChatDock provide?",
        )
        self.assertTrue(cached_again)
        logs = list(store.chat_logs.values())
        self.assertEqual(len(logs), 2)
        self.assertEqual(sum(1 for log in logs if log.cached), 1)


if __name__ == "__main__":
    unittest.main()
