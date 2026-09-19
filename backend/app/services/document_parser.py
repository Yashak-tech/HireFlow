import os
import re
from dataclasses import dataclass
from typing import Optional
from fastapi import HTTPException, status
import pypdf
import pdfplumber
import docx


@dataclass
class ParsedDocument:
    raw_text: str
    char_count: int
    word_count: int
    page_count: int
    file_format: str


def normalize_document_text(text: str) -> str:
    """
    Normalize text whitespace, carriage returns, non-breaking spaces,
    and collapse excessive empty lines while preserving section hierarchy.
    """
    if not text:
        return ""
    
    # Normalize carriage returns and unicode spaces
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\xa0", " ").replace("\u200b", "")
    
    # Replace multiple spaces/tabs within lines
    lines = []
    for line in text.split("\n"):
        # Strip trailing whitespace and collapse interior tabs/spaces
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(cleaned_line)
    
    joined = "\n".join(lines)
    # Collapse 3 or more newlines to at most 2 newlines (preserve paragraphs)
    normalized = re.sub(r"\n{3,}", "\n\n", joined).strip()
    return normalized


def extract_pdf_text(file_path: str) -> ParsedDocument:
    """
    Extract text from a PDF file using pypdf with fallback to pdfplumber.
    If no readable text is found (e.g., scanned/image-only PDF),
    raises HTTP 422 with strict authoritative message.
    """
    extracted_text_pages = []
    page_count = 0

    # 1. First attempt with pypdf
    try:
        reader = pypdf.PdfReader(file_path)
        page_count = len(reader.pages)
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                extracted_text_pages.append(t)
    except Exception as e:
        # Fall back or re-try with pdfplumber before declaring corrupted
        pass

    # 2. If pypdf produced no or minimal text, attempt with pdfplumber
    if not extracted_text_pages or sum(len(p.strip()) for p in extracted_text_pages) < 20:
        try:
            with pdfplumber.open(file_path) as pdf:
                page_count = max(page_count, len(pdf.pages))
                plumber_pages = []
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    if t.strip():
                        plumber_pages.append(t)
                if plumber_pages:
                    extracted_text_pages = plumber_pages
        except Exception:
            pass

    full_raw = "\n\n".join(extracted_text_pages)
    normalized = normalize_document_text(full_raw)

    # Check for empty / scanned PDF
    if not normalized or len(normalized.strip()) == 0:
        raise HTTPException(
            status_code=422,
            detail="Unreadable PDF: Please provide a text-based PDF or DOCX format.",
        )

    words = re.findall(r"\b\w+\b", normalized)
    return ParsedDocument(
        raw_text=normalized,
        char_count=len(normalized),
        word_count=len(words),
        page_count=max(page_count, 1),
        file_format="pdf",
    )


def extract_docx_text(file_path: str) -> ParsedDocument:
    """Extract text from a Word DOCX document."""
    try:
        doc = docx.Document(file_path)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail="Malformed or corrupted document could not be processed.",
        )

    elements = []
    # Extract from paragraphs
    for p in doc.paragraphs:
        if p.text.strip():
            elements.append(p.text.strip())

    # Extract from tables
    for table in doc.tables:
        for row in table.rows:
            row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_cells:
                elements.append(" | ".join(row_cells))

    full_raw = "\n\n".join(elements)
    normalized = normalize_document_text(full_raw)

    if not normalized or len(normalized.strip()) == 0:
        raise HTTPException(
            status_code=422,
            detail="Document contains no readable text.",
        )

    words = re.findall(r"\b\w+\b", normalized)
    return ParsedDocument(
        raw_text=normalized,
        char_count=len(normalized),
        word_count=len(words),
        page_count=1,
        file_format="docx",
    )


def extract_txt_text(file_path: str) -> ParsedDocument:
    """Extract text from a plain text file using native UTF-8 with fallbacks."""
    content = None
    for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        raise HTTPException(
            status_code=422,
            detail="Unable to decode text document with supported encodings.",
        )

    normalized = normalize_document_text(content)
    if not normalized or len(normalized.strip()) == 0:
        raise HTTPException(
            status_code=422,
            detail="Document contains no readable text.",
        )

    words = re.findall(r"\b\w+\b", normalized)
    return ParsedDocument(
        raw_text=normalized,
        char_count=len(normalized),
        word_count=len(words),
        page_count=1,
        file_format="txt",
    )


def parse_document_file(file_path: str, file_type: Optional[str] = None) -> ParsedDocument:
    """
    Parse a stored document file (PDF, DOCX, TXT) and return structured text and metadata.
    Validates file existence, format, and readable content.
    """
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Stored document file not found at path: {file_path}",
        )

    ext = os.path.splitext(file_path)[1].lower()
    # Also support mime type hints if extension is ambiguous
    if ext == ".pdf" or file_type == "application/pdf":
        return extract_pdf_text(file_path)
    elif ext in [".docx", ".doc"] or file_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        return extract_docx_text(file_path)
    elif ext == ".txt" or file_type == "text/plain":
        return extract_txt_text(file_path)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported document format '{ext}'. Only PDF, DOCX, and TXT are supported.",
        )
