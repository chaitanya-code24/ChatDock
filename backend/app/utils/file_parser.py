from __future__ import annotations

from fastapi import HTTPException, status


def parse_document(file_name: str, suffix: str, payload: bytes) -> str:
    if suffix in {".txt", ".md"}:
        return payload.decode("utf-8", errors="ignore")
    if suffix == ".pdf":
        return _extract_pdf_text(payload, file_name)
    if suffix == ".docx":
        return _extract_docx_text(payload, file_name)
    return ""


def _extract_pdf_text(payload: bytes, file_name: str) -> str:
    try:
        from pypdf import PdfReader  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"PDF parsing requires pypdf to be installed before uploading {file_name}.",
        ) from exc

    from io import BytesIO

    reader = PdfReader(BytesIO(payload))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_docx_text(payload: bytes, file_name: str) -> str:
    try:
        import docx  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"DOCX parsing requires python-docx to be installed before uploading {file_name}.",
        ) from exc

    from io import BytesIO

    doc = docx.Document(BytesIO(payload))
    return "\n".join(paragraph.text for paragraph in doc.paragraphs)

