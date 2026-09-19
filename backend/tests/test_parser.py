import os
import tempfile
import pytest
from fastapi import HTTPException
from pypdf import PdfWriter
import docx

from app.services.document_parser import (
    parse_document_file,
    normalize_document_text,
    extract_pdf_text,
    extract_docx_text,
    extract_txt_text,
)


def create_minimal_text_pdf(path: str, text: str = "Jane Doe Senior Python Engineer"):
    """Generate a minimal valid PDF with extractable text."""
    pdf_bytes = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length " + str(len(text) + 30).encode() + b">>stream\n"
        b"BT /F1 12 Tf 72 712 Td (" + text.encode() + b") Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n"
        b"0000000101 00000 n \n0000000212 00000 n \n0000000283 00000 n \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n377\n%%EOF\n"
    )
    with open(path, "wb") as f:
        f.write(pdf_bytes)


def test_normalize_whitespace():
    raw = "  Hello \t world!  \r\n\r\n\r\n\r\nNext   line.\xa0\xa0\n"
    normalized = normalize_document_text(raw)
    assert "Hello world!" in normalized
    assert "Next line." in normalized
    assert "\r" not in normalized
    assert "\xa0" not in normalized


def test_extract_valid_txt(tmp_path):
    txt_file = tmp_path / "resume.txt"
    sample_text = (
        "Alice Smith\n"
        "Senior Backend Developer with 6 years of experience.\n"
        "Skills: Python, FastAPI, Docker, PostgreSQL, AWS.\n"
        "Experience: Built scalable microservices handling 10k requests/sec."
    )
    txt_file.write_text(sample_text, encoding="utf-8")

    result = parse_document_file(str(txt_file))
    assert result.file_format == "txt"
    assert "Alice Smith" in result.raw_text
    assert "Python" in result.raw_text
    assert result.char_count > 50
    assert result.word_count > 10


def test_extract_valid_docx(tmp_path):
    docx_file = tmp_path / "resume.docx"
    doc = docx.Document()
    doc.add_heading("Bob Johnson - Full Stack Engineer", level=1)
    doc.add_paragraph("Experienced in React, TypeScript, Node.js, and GraphQL.")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Education: BS Computer Science"
    table.rows[0].cells[1].text = "GPA: 3.9"
    doc.save(str(docx_file))

    result = parse_document_file(str(docx_file))
    assert result.file_format == "docx"
    assert "Bob Johnson" in result.raw_text
    assert "React" in result.raw_text
    assert "Education: BS Computer Science" in result.raw_text


def test_extract_valid_pdf(tmp_path):
    pdf_file = tmp_path / "resume.pdf"
    create_minimal_text_pdf(str(pdf_file), "Carol White Lead Architect Kubernetes Cloud")

    result = parse_document_file(str(pdf_file))
    assert result.file_format == "pdf"
    assert "Carol White" in result.raw_text
    assert "Kubernetes" in result.raw_text
    assert result.page_count >= 1


def test_unreadable_scanned_pdf(tmp_path):
    """
    Test scanned or image-only PDF containing no readable text stream.
    Must return HTTP 422 with strict authoritative message:
    'Unreadable PDF: Please provide a text-based PDF or DOCX format.'
    """
    pdf_file = tmp_path / "scanned_blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    with open(str(pdf_file), "wb") as f:
        writer.write(f)

    with pytest.raises(HTTPException) as exc_info:
        parse_document_file(str(pdf_file))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "Unreadable PDF: Please provide a text-based PDF or DOCX format."


def test_empty_txt_file(tmp_path):
    empty_file = tmp_path / "empty.txt"
    empty_file.write_text("   \n\n\t  ", encoding="utf-8")

    with pytest.raises(HTTPException) as exc_info:
        parse_document_file(str(empty_file))

    assert exc_info.value.status_code == 422
    assert "no readable text" in exc_info.value.detail.lower()


def test_empty_docx_file(tmp_path):
    empty_docx = tmp_path / "empty.docx"
    doc = docx.Document()
    doc.save(str(empty_docx))

    with pytest.raises(HTTPException) as exc_info:
        parse_document_file(str(empty_docx))

    assert exc_info.value.status_code == 422
    assert "no readable text" in exc_info.value.detail.lower()


def test_unsupported_file_format(tmp_path):
    image_file = tmp_path / "profile.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")

    with pytest.raises(HTTPException) as exc_info:
        parse_document_file(str(image_file))

    assert exc_info.value.status_code == 400
    assert "Unsupported document format" in exc_info.value.detail


def test_nonexistent_file():
    with pytest.raises(HTTPException) as exc_info:
        parse_document_file("c:/nonexistent/path/to/missing_file.pdf")

    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_malformed_docx_file(tmp_path):
    corrupt_docx = tmp_path / "corrupt.docx"
    corrupt_docx.write_bytes(b"PK\x03\x04not_a_valid_zip_archive")

    with pytest.raises(HTTPException) as exc_info:
        parse_document_file(str(corrupt_docx))

    assert exc_info.value.status_code == 422
    assert "corrupted" in exc_info.value.detail.lower()
