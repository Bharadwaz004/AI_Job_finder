"""
Resume text extraction from PDF and DOCX files.
Uses PyMuPDF for PDFs, python-docx for Word documents.
"""

import io
from pathlib import Path

from utils.logger import setup_logger
from utils.exceptions import FileValidationError, ResumeParsingError

log = setup_logger("resume_parser")

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_file(filename: str, content_type: str, size: int, max_size: int):
    """Validate uploaded file before processing."""
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    if content_type and content_type not in ALLOWED_MIME_TYPES:
        # Some browsers send generic types — allow if extension is valid
        log.warning(f"Unexpected MIME type: {content_type} for {filename}")

    if size > max_size:
        raise FileValidationError(
            f"File too large ({size / 1024 / 1024:.1f}MB). Max: {max_size / 1024 / 1024:.0f}MB"
        )


async def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page_num, page in enumerate(doc):
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)

        doc.close()
        full_text = "\n\n".join(text_parts).strip()

        if not full_text:
            raise ResumeParsingError(
                "Could not extract text from PDF. The file may be image-based or empty."
            )

        log.info(f"Extracted {len(full_text)} chars from PDF ({page_num + 1} pages)")
        return full_text

    except ResumeParsingError:
        raise
    except Exception as e:
        log.error(f"PDF extraction failed: {e}")
        raise ResumeParsingError(f"Failed to parse PDF: {str(e)}")


async def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX using python-docx."""
    try:
        from docx import Document

        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        full_text = "\n".join(paragraphs).strip()

        if not full_text:
            raise ResumeParsingError("Could not extract text from DOCX. File may be empty.")

        log.info(f"Extracted {len(full_text)} chars from DOCX ({len(paragraphs)} paragraphs)")
        return full_text

    except ResumeParsingError:
        raise
    except Exception as e:
        log.error(f"DOCX extraction failed: {e}")
        raise ResumeParsingError(f"Failed to parse DOCX: {str(e)}")


async def extract_text(file_bytes: bytes, filename: str) -> str:
    """Route to the correct parser based on file extension."""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return await extract_text_from_pdf(file_bytes)
    elif ext == ".docx":
        return await extract_text_from_docx(file_bytes)
    else:
        raise FileValidationError(f"Unsupported extension: {ext}")
