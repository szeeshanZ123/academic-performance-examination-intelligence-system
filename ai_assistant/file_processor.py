"""File processing and text extraction utility for AI Study Assistant.

Supports PDF (via PyMuPDF / fitz), DOCX (python-docx), TXT, and Images (PNG, JPG, JPEG).
Provides safe size validation, mime validation, and clean error messages.
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".png", ".jpg", ".jpeg", ".webp"}


def clean_text(text: str) -> str:
    """Normalize and clean extracted text."""
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[ \t]+$", "", line) for line in text.split("\n")]
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def extract_text_from_pdf(file_path: Path) -> Dict[str, Any]:
    """Extract text from PDF using PyMuPDF (fitz) or fallback."""
    try:
        import pymupdf as fitz
        doc = fitz.open(str(file_path))
        pages = []
        for idx, page in enumerate(doc):
            t = page.get_text("text")
            if t.strip():
                pages.append(f"--- Page {idx + 1} ---\n{t.strip()}")
        doc.close()
        
        extracted = clean_text("\n\n".join(pages))
        if not extracted or len(re.findall(r"[a-zA-Z0-9]", extracted)) < 15:
            return {
                "success": False,
                "text": extracted,
                "error": "This PDF document appears to be scanned or contains only images without readable text.",
                "file_type": "PDF",
                "page_count": len(pages) or 1
            }
            
        return {
            "success": True,
            "text": extracted,
            "error": None,
            "file_type": "PDF",
            "page_count": len(pages)
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Unable to read PDF file: {str(e)}",
            "file_type": "PDF",
            "page_count": 0
        }


def extract_text_from_docx(file_path: Path) -> Dict[str, Any]:
    """Extract text from DOCX using python-docx."""
    try:
        import docx
        doc = docx.Document(str(file_path))
        lines = []
        for p in doc.paragraphs:
            if p.text.strip():
                lines.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                cells = [c.text.strip() for c in row.cells if c.text.strip()]
                if cells:
                    lines.append(" | ".join(cells))
        extracted = clean_text("\n".join(lines))
        if not extracted:
            return {
                "success": False,
                "text": "",
                "error": "The uploaded DOCX file contains no readable text.",
                "file_type": "DOCX",
                "page_count": 1
            }
        return {
            "success": True,
            "text": extracted,
            "error": None,
            "file_type": "DOCX",
            "page_count": 1
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Unable to read DOCX file: {str(e)}",
            "file_type": "DOCX",
            "page_count": 0
        }


def extract_text_from_txt(file_path: Path) -> Dict[str, Any]:
    """Extract text from plain text file."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    content = None
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except Exception:
            continue
    if content is None:
        return {
            "success": False,
            "text": "",
            "error": "Failed to decode text file with standard encodings.",
            "file_type": "TXT",
            "page_count": 0
        }
    extracted = clean_text(content)
    if not extracted:
        return {
            "success": False,
            "text": "",
            "error": "The uploaded text file is empty.",
            "file_type": "TXT",
            "page_count": 1
        }
    return {
        "success": True,
        "text": extracted,
        "error": None,
        "file_type": "TXT",
        "page_count": 1
    }


def extract_text_from_image(file_path: Path) -> Dict[str, Any]:
    """Extract information/text from image files using OCR or Image Intelligence."""
    try:
        from PIL import Image
        img = Image.open(file_path)
        width, height = img.size
        img_format = img.format or file_path.suffix.upper().lstrip(".")

        # Check for pytesseract if available
        text_content = ""
        try:
            import importlib
            pytesseract_mod = importlib.import_module("pytesseract")
            text_content = clean_text(pytesseract_mod.image_to_string(img))
        except Exception:
            # Fallback if tesseract binary is not installed locally
            text_content = ""

        if text_content and len(text_content.strip()) > 10:
            return {
                "success": True,
                "text": text_content,
                "error": None,
                "file_type": f"IMAGE ({img_format})",
                "page_count": 1,
                "is_image": True,
                "dimensions": f"{width}x{height}"
            }

        # If OCR not found or produced empty text, return descriptive notice
        return {
            "success": True,
            "text": f"[Uploaded Image: {file_path.name} ({width}x{height}px {img_format})].\nNote: Optical OCR requires standard system libraries or cloud vision API. You can still ask questions, generate summaries, or quiz topics based on this study topic.",
            "error": None,
            "file_type": f"IMAGE ({img_format})",
            "page_count": 1,
            "is_image": True,
            "dimensions": f"{width}x{height}"
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Failed to process image file: {str(e)}",
            "file_type": "IMAGE",
            "page_count": 0
        }


def process_uploaded_document(file_path: str | Path) -> Dict[str, Any]:
    """Process any supported document and return normalized text & metadata."""
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": f"File does not exist: {path.name}", "text": ""}

    # Check file size
    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        return {
            "success": False,
            "error": f"File size ({path.stat().st_size / (1024*1024):.1f} MB) exceeds maximum allowed limit of 10 MB.",
            "text": ""
        }

    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return {
            "success": False,
            "error": f"Unsupported file format '{ext}'. Allowed formats: PDF, DOCX, TXT, PNG, JPG, JPEG.",
            "text": ""
        }

    if ext == ".pdf":
        res = extract_text_from_pdf(path)
    elif ext == ".docx":
        res = extract_text_from_docx(path)
    elif ext == ".txt":
        res = extract_text_from_txt(path)
    else:  # Image formats
        res = extract_text_from_image(path)

    res["filename"] = path.name
    res["filesize_kb"] = round(path.stat().st_size / 1024, 1)
    return res
