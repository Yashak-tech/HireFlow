import os
import uuid
import re
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "text/plain",
    "application/octet-stream",  # Often sent by browsers for binary docs
}
MAX_FILE_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024  # 10MB


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename to remove path traversal sequences and special characters."""
    # Strip directory components
    basename = os.path.basename(filename)
    # Remove null bytes and traversal attempts
    basename = basename.replace("\x00", "").replace("..", "")
    # Keep only safe alphanumeric, dots, dashes, underscores
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', basename)
    return sanitized or "resume_upload"


async def validate_and_save_resume_file(upload_file: UploadFile) -> Tuple[str, str, str, int]:
    """
    Validate file extension, mime type, and file size.
    Saves file to settings.UPLOAD_DIR using a secure UUID-prefixed filename.

    Returns:
        Tuple of (original_filename, saved_file_path, file_type, file_size_bytes)
    """
    original_name = upload_file.filename or "uploaded_resume.pdf"
    ext = os.path.splitext(original_name)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{ext}'. Only PDF, DOCX, and TXT files are allowed.",
        )

    # Read content to verify size
    content = await upload_file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size ({file_size / (1024 * 1024):.2f}MB) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=422,
            detail="Uploaded file is empty (0 bytes).",
        )

    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Generate safe UUID-based filename to prevent path traversal & overwrite
    safe_basename = sanitize_filename(original_name)
    stored_filename = f"{uuid.uuid4()}_{safe_basename}"
    storage_path = os.path.join(settings.UPLOAD_DIR, stored_filename)

    # Write file to disk
    with open(storage_path, "wb") as f:
        f.write(content)

    # Normalize mime type
    mime_type = upload_file.content_type or "application/octet-stream"
    if ext == ".pdf":
        mime_type = "application/pdf"
    elif ext == ".docx":
        mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    elif ext == ".txt":
        mime_type = "text/plain"

    return original_name, storage_path, mime_type, file_size
