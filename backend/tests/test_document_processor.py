import unittest

from app.rag.document_processor import (
    build_structured_chunks,
    chunk_section,
    filter_sections,
    is_noise_chunk,
    is_heading,
    normalize_text,
    remove_repeated_lines,
    split_into_sections,
)


class DocumentProcessorTests(unittest.TestCase):
    def test_remove_repeated_lines_drops_headers_and_footers(self) -> None:
        text = "\n".join(
            [
                "HDFC LIFE INSURANCE COMPANY",
                "Page 1 of 10",
                "1. Nomination",
                "Nomination allows assigning a beneficiary.",
                "HDFC LIFE INSURANCE COMPANY",
                "Page 2 of 10",
                "2. Claims",
                "Claims should be filed within the stipulated period.",
                "HDFC LIFE INSURANCE COMPANY",
                "Page 3 of 10",
                "HDFC LIFE INSURANCE COMPANY",
                "Page 4 of 10",
                "HDFC LIFE INSURANCE COMPANY",
                "Page 5 of 10",
                "HDFC LIFE INSURANCE COMPANY",
                "Page 6 of 10",
            ]
        )
        cleaned = remove_repeated_lines(text)
        self.assertNotIn("HDFC LIFE INSURANCE COMPANY", cleaned)
        self.assertNotIn("Page 1 of 10", cleaned)

    def test_split_into_sections_groups_content_under_headings(self) -> None:
        text = (
            "1. Nomination\n"
            "Nomination allows assigning a beneficiary under the policy.\n\n"
            "2. Claims\n"
            "Claims should be filed within 30 days."
        )
        sections = split_into_sections(text)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0]["heading"], "Nomination")
        self.assertIn("beneficiary", sections[0]["content"].lower())
        self.assertEqual(sections[1]["heading"], "Claims")

    def test_filter_sections_removes_boilerplate(self) -> None:
        sections = [
            {"heading": "Annexure A", "content": "a" * 200},
            {"heading": "Nomination", "content": "Nomination allows assigning a beneficiary under the policy."},
            {"heading": "Tiny", "content": "short"},
        ]
        filtered = filter_sections(sections)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["heading"], "Nomination")

    def test_noise_chunk_detection_filters_contents(self) -> None:
        self.assertTrue(is_noise_chunk({"heading": "Contents", "content": "A" * 80}))
        self.assertFalse(is_noise_chunk({"heading": "Logical Access Controls", "content": "A" * 80}))

    def test_chunk_section_preserves_small_section_as_single_chunk(self) -> None:
        section = {
            "heading": "Logical Access Controls",
            "content": "Sentence one is here. Sentence two explains passwords. Sentence three explains accounts.",
        }
        chunks = chunk_section(section, max_chars=55)
        self.assertEqual(len(chunks), 1)
        self.assertTrue(all(chunk["heading"] == "Logical Access Controls" for chunk in chunks))

    def test_build_structured_chunks_adds_metadata(self) -> None:
        text = (
            "TWOC IT Policies\n"
            "TWOC IT Policies\n"
            "TWOC IT Policies\n"
            "TWOC IT Policies\n"
            "TWOC IT Policies\n"
            "TWOC IT Policies\n"
            "1. Logical Access Controls\n"
            "No person would access any application unless specifically authorized. "
            "Each user ID is unique and passwords must be protected.\n"
        )
        chunks = build_structured_chunks(text, source="it-policy.pdf")
        self.assertTrue(chunks)
        self.assertEqual(chunks[0].heading, "Logical Access Controls")
        self.assertEqual(chunks[0].metadata["topic"], "logical_access_controls")
        self.assertTrue(chunks[0].metadata["section_id"])
        self.assertEqual(chunks[0].metadata["type"], "policy_section")
        self.assertEqual(chunks[0].metadata["source"], "it-policy.pdf")
        self.assertIn("Heading: Logical Access Controls", chunks[0].to_storage_text())
        self.assertIn("SectionId:", chunks[0].to_storage_text())

    def test_heading_detection(self) -> None:
        self.assertTrue(is_heading("1. Nomination"))
        self.assertTrue(is_heading("LOGICAL ACCESS CONTROLS"))
        self.assertTrue(is_heading("Physical Access Controls"))
        self.assertFalse(is_heading("This is a long descriptive sentence that should not be treated as a heading"))

    def test_normalize_text_repairs_ocr_word_breaks(self) -> None:
        normalized = normalize_text("Pr oposal   Form\n\nLogical   Access   Controls")
        self.assertIn("Proposal Form", normalized)
        self.assertIn("Logical Access Controls", normalized)


if __name__ == "__main__":
    unittest.main()
