import unittest

from app.rag.context_validator import validate_context


class RagRelevanceTests(unittest.TestCase):
    def test_validate_context_rejects_irrelevant_chunk(self) -> None:
        query = "return and refunds"
        chunks = [
            {
                "score": 0.2,
                "excerpt": "server room and other infrastructure facilities at the Head Office. CIO would create necessary plans.",
            }
        ]
        self.assertFalse(validate_context(query, chunks))

    def test_validate_context_accepts_relevant_chunk(self) -> None:
        query = "return and refunds"
        chunks = [
            {
                "score": 0.2,
                "excerpt": "Refunds are processed within 7 business days. Products can be returned within 7 days of delivery.",
            }
        ]
        self.assertTrue(validate_context(query, chunks))


if __name__ == "__main__":
    unittest.main()

