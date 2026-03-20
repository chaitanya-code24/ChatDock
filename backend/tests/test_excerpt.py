import unittest

from app.services.chat_service import ChatService


class ExcerptTests(unittest.TestCase):
    def test_excerpt_finds_term_late_in_text(self) -> None:
        text = "intro " + ("x" * 1200) + " password policy states that passwords must be rotated"
        ex = ChatService._excerpt_for_query(text, "password policy", max_len=300)
        self.assertIn("password", ex.lower())
        self.assertLessEqual(len(ex), 400)

    def test_excerpt_prefers_phrase_over_generic_term(self) -> None:
        text = (
            "Nature and purpose of the IT Policy document. A policy is a high level statement of Management intent. "
            "Later the document defines Service Level Management and related SLAs."
        )
        ex = ChatService._excerpt_for_query(text, "what is service level management", max_len=260)
        self.assertIn("service level", ex.lower())


if __name__ == "__main__":
    unittest.main()
