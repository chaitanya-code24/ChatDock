from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from app.rag.chunking import TOKEN_PATTERN, chunk_preserving_section, estimate_token_count


NUMBERED_HEADING = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+[A-Z][\w /&(),:-]{1,}$")
LEADING_NUMBER = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s+(.*)$")
PAGE_MARKER = re.compile(r"^\s*page\s+\d+\s+(?:of|/)\s+\d+\s*$", re.IGNORECASE)
OCR_BROKEN_WORD = re.compile(r"\b([A-Za-z]{1,3})\s+([A-Za-z]{3,})\b")
INLINE_SPACES = re.compile(r"[ \t]+")


@dataclass(slots=True)
class StructuredChunk:
    heading: str
    text: str
    metadata: dict[str, str]

    def to_storage_text(self) -> str:
        heading = self.heading.strip() or "General"
        topic = self.metadata.get("topic", heading.lower())
        chunk_type = self.metadata.get("type", "policy_section")
        normalized_heading = self.metadata.get("normalized_heading", heading.lower())
        section_id = self.metadata.get("section_id", normalized_heading)
        body = self.text.strip()
        return (
            f"Title: {heading}\n"
            f"Heading: {heading}\n"
            f"NormalizedHeading: {normalized_heading}\n"
            f"SectionId: {section_id}\n"
            f"Topic: {topic}\n"
            f"Type: {chunk_type}\n\n{body}"
        )


def remove_repeated_lines(text: str) -> str:
    lines = [line.strip() for line in text.splitlines()]
    normalized_counts: dict[str, int] = {}
    for line in lines:
        normalized = _normalize_line_for_count(line)
        if normalized:
            normalized_counts[normalized] = normalized_counts.get(normalized, 0) + 1

    kept: list[str] = []
    for line in lines:
        normalized = _normalize_line_for_count(line)
        if not normalized:
            continue
        if normalized_counts.get(normalized, 0) > 5:
            continue
        if PAGE_MARKER.match(normalized):
            continue
        kept.append(line)
    return "\n".join(kept)


def normalize_text(text: str) -> str:
    output: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.replace("\xa0", " ").strip()
        if not line:
            output.append("")
            continue

        line = INLINE_SPACES.sub(" ", line)

        # Repair common OCR word breaks while keeping line structure intact.
        for _ in range(6):
            next_line = OCR_BROKEN_WORD.sub(_merge_ocr_words, line)
            if next_line == line:
                break
            line = next_line

        line = re.sub(r"\s+([,.;:!?])", r"\1", line)
        output.append(line.strip())

    # Collapse repeated blank lines.
    collapsed: list[str] = []
    blank = False
    for line in output:
        if not line:
            if blank:
                continue
            blank = True
            collapsed.append("")
            continue
        blank = False
        collapsed.append(line)
    return "\n".join(collapsed).strip()


def is_heading(line: str) -> bool:
    candidate = line.strip()
    if not candidate:
        return False
    if len(candidate) > 120:
        return False
    if NUMBERED_HEADING.match(candidate):
        return True
    words = candidate.split()
    if len(words) > 8:
        return False
    if candidate.isupper() and len(words) <= 8:
        return True
    if _is_title_case_heading(candidate) and len(words) <= 8:
        return True
    return False


def split_into_sections(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_heading = "General"
    current_lines: list[str] = []

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current_lines and current_lines[-1] != "":
                current_lines.append("")
            continue

        if is_heading(stripped):
            if current_lines:
                sections.append({"heading": current_heading, "content": _finalize_section_content(current_lines)})
            current_heading = _clean_heading(stripped)
            current_lines = []
            continue

        current_lines.append(stripped)

    if current_lines:
        sections.append({"heading": current_heading, "content": _finalize_section_content(current_lines)})

    return sections


def filter_sections(sections: list[dict[str, str]]) -> list[dict[str, str]]:
    blocked_headings = ("annexure", "policy schedule", "section 38", "section 39", "contents", "index")
    filtered: list[dict[str, str]] = []
    for section in sections:
        heading = _clean_heading((section.get("heading") or "").strip())
        content = (section.get("content") or "").strip()
        if not content or len(content) < 50:
            continue
        if any(blocked in heading.lower() for blocked in blocked_headings):
            continue
        candidate = {"heading": heading or "General", "content": content}
        if is_noise_chunk(candidate):
            continue
        filtered.append(candidate)
    return filtered


def chunk_section(section: dict[str, str], max_chars: int = 800) -> list[dict[str, str]]:
    heading = _clean_heading((section.get("heading") or "General").strip())
    content = (section.get("content") or "").strip()
    if not content:
        return []

    preserved_chunks = chunk_preserving_section(content, max_tokens=500)
    return [{"heading": heading, "text": chunk.strip()} for chunk in preserved_chunks if chunk.strip()]


def build_structured_chunks(text: str, source: str) -> list[StructuredChunk]:
    processed_text = normalize_text(remove_repeated_lines(text))
    sections = filter_sections(split_into_sections(processed_text))
    if not sections:
        # Fallback for simple/unstructured documents.
        fallback_text = processed_text.strip()
        if not fallback_text:
            return []
        return [
            StructuredChunk(
                heading="General",
                text=fallback_text,
                metadata={
                    "topic": "general",
                    "normalized_heading": "general",
                    "section_id": _section_id_for(source, "general"),
                    "type": "policy_section",
                    "source": source,
                },
            )
        ]

    structured: list[StructuredChunk] = []
    for section in sections:
        section_heading = _clean_heading(section["heading"].strip() or "General")
        section_id = _section_id_for(source, section_heading)
        for chunk in chunk_section(section):
            heading = _clean_heading(chunk["heading"].strip() or "General")
            body = chunk["text"].strip()
            if estimate_token_count(body) <= 0:
                continue
            structured.append(
                StructuredChunk(
                    heading=heading,
                    text=body,
                    metadata={
                        "topic": _normalize_topic(heading),
                        "normalized_heading": heading.lower(),
                        "section_id": section_id,
                        "type": "policy_section",
                        "source": source,
                    },
                )
            )
    return structured


def extract_chunk_metadata(text: str) -> dict[str, str]:
    heading_match = re.search(r"^Heading:\s*(.+)$", text, re.MULTILINE)
    topic_match = re.search(r"^Topic:\s*(.+)$", text, re.MULTILINE)
    type_match = re.search(r"^Type:\s*(.+)$", text, re.MULTILINE)
    normalized_heading_match = re.search(r"^NormalizedHeading:\s*(.+)$", text, re.MULTILINE)
    section_id_match = re.search(r"^SectionId:\s*(.+)$", text, re.MULTILINE)
    body = text.split("\n\n", 1)[1].strip() if "\n\n" in text else text.strip()
    heading = heading_match.group(1).strip() if heading_match else "General"
    return {
        "heading": heading,
        "normalized_heading": normalized_heading_match.group(1).strip() if normalized_heading_match else heading.lower(),
        "section_id": section_id_match.group(1).strip() if section_id_match else heading.lower(),
        "topic": topic_match.group(1).strip() if topic_match else "general",
        "type": type_match.group(1).strip() if type_match else "policy_section",
        "body": body,
    }


def is_noise_chunk(section: dict[str, str]) -> bool:
    heading = _clean_heading((section.get("heading") or "").strip()).lower()
    text = (section.get("content") or section.get("text") or "").strip()
    if len(text) < 50:
        return True
    if any(marker in heading for marker in ("contents", "index")):
        return True
    return False


def _normalize_line_for_count(line: str) -> str:
    normalized = INLINE_SPACES.sub(" ", line.strip())
    if len(normalized) < 3:
        return ""
    return normalized


def _merge_ocr_words(match: re.Match[str]) -> str:
    left = match.group(1)
    right = match.group(2)
    if left.istitle() or right.istitle() or left.isupper():
        return f"{left}{right}"
    if len(left) <= 2:
        return f"{left}{right}"
    return match.group(0)


def _is_title_case_heading(line: str) -> bool:
    words = [word for word in re.split(r"\s+", line) if word]
    if not words:
        return False
    capitalized = 0
    for word in words:
        cleaned = word.strip("()[]{}.,:;/-")
        if not cleaned:
            continue
        if cleaned[0].isupper():
            capitalized += 1
    return capitalized >= max(1, len(words) - 1)


def _finalize_section_content(lines: list[str]) -> str:
    content = "\n".join(lines).strip()
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content


def _split_sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [chunk.strip() for chunk in chunks if chunk and chunk.strip()]


def _normalize_topic(heading: str) -> str:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(heading) if token]
    return "_".join(tokens) if tokens else "general"


def _clean_heading(heading: str) -> str:
    candidate = INLINE_SPACES.sub(" ", (heading or "").strip())
    if not candidate:
        return "General"
    match = LEADING_NUMBER.match(candidate)
    if match:
        candidate = match.group(1).strip()
    candidate = candidate.strip(" -:.")
    return candidate or "General"


def _section_id_for(source: str, heading: str) -> str:
    normalized = _normalize_topic(heading)
    return hashlib.sha1(f"{source}:{normalized}".encode("utf-8")).hexdigest()[:16]
