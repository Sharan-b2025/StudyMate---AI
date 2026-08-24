"""
File Processing Service
------------------------
Extracts raw text from uploaded study materials.
Supports: PDF, DOCX, TXT, PNG/JPG/JPEG (via OCR).

All extraction failures are caught and returned as (None, error_message)
so upload flows never crash on a corrupted/unsupported file.
"""
import os
from flask import current_app


class ExtractionError(Exception):
    pass


def allowed_file(filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in current_app.config["ALLOWED_EXTENSIONS"], ext


def extract_text(filepath, file_type):
    try:
        if file_type == "pdf":
            return _extract_pdf(filepath), None
        if file_type == "docx":
            return _extract_docx(filepath), None
        if file_type == "txt":
            return _extract_txt(filepath), None
        if file_type in ("png", "jpg", "jpeg"):
            return _extract_image(filepath), None
        return None, f"Unsupported file type: {file_type}"
    except Exception as exc:  # noqa: BLE001 - we want to catch everything here
        return None, f"Could not process file: {exc}"


def _extract_pdf(filepath):
    from pypdf import PdfReader

    reader = PdfReader(filepath)
    pages = []
    for page in reader.pages:
        content = page.extract_text() or ""
        pages.append(content)
    text = "\n".join(pages).strip()
    if not text:
        raise ExtractionError("No extractable text found (the PDF may be scanned/image-only).")
    return text


def _extract_docx(filepath):
    import docx

    document = docx.Document(filepath)
    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    text = "\n".join(parts).strip()
    if not text:
        raise ExtractionError("The document appears to be empty.")
    return text


def _extract_txt(filepath):
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read().strip()
    if not text:
        raise ExtractionError("The text file is empty.")
    return text


def _extract_image(filepath):
    import pytesseract
    from PIL import Image

    tesseract_cmd = current_app.config.get("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    image = Image.open(filepath)
    text = pytesseract.image_to_string(image).strip()
    if not text:
        raise ExtractionError("No text could be detected in the image.")
    return text
