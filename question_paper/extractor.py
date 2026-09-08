"""Document text extraction module for question papers.

Supports PDF (via PyMuPDF / fitz), DOCX (via python-docx), and TXT formats.
Detects image-only / scanned documents cleanly without crashing.
"""

import re
from pathlib import Path


def normalize_extracted_text(text: str) -> str:
    """Normalize extracted document text without altering question phrasing."""
    if not text:
        return ""
    
    # Replace non-breaking spaces and special unicode spaces with standard space
    text = text.replace("\xa0", " ").replace("\u200b", "")
    
    # Normalize line breaks
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove trailing spaces on each line
    lines = [re.sub(r"[ \t]+$", "", line) for line in text.split("\n")]
    
    # Join and reduce multiple consecutive blank lines to at most two
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    return cleaned.strip()


def extract_from_pdf(file_path: Path) -> dict:
    """Extract text from a PDF document using PyMuPDF (fitz) or pypdf fallback."""
    full_text = []
    page_count = 0
    
    try:
        import pymupdf as fitz
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        for page in doc:
            full_text.append(page.get_text("text"))
        doc.close()
    except Exception as e_fitz:
        # Fallback to pypdf if PyMuPDF encounters an unexpected issue
        try:
            import pypdf
            reader = pypdf.PdfReader(str(file_path))
            page_count = len(reader.pages)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    full_text.append(extracted)
        except Exception as e_pypdf:
            return {
                "success": False,
                "text": "",
                "page_count": 0,
                "file_type": "PDF",
                "is_scanned": False,
                "error": f"Failed to read PDF file: {e_fitz}"
            }

    raw_text = "\n".join(full_text)
    cleaned_text = normalize_extracted_text(raw_text)
    
    # Scanned document detection: if pages exist but extracted text is negligible or contains no letters
    alphabetic_chars = re.findall(r"[a-zA-Z]", cleaned_text)
    if page_count > 0 and len(alphabetic_chars) < 25:
        return {
            "success": False,
            "text": cleaned_text,
            "page_count": page_count,
            "file_type": "PDF",
            "is_scanned": True,
            "error": "This document appears to be scanned/image-based. OCR support is required for full analysis."
        }
    
    return {
        "success": True,
        "text": cleaned_text,
        "page_count": page_count,
        "file_type": "PDF",
        "is_scanned": False,
        "error": None
    }


def extract_from_docx(file_path: Path) -> dict:
    """Extract text from a DOCX document using python-docx."""
    try:
        import docx
        doc = docx.Document(str(file_path))
        
        paragraphs = []
        for p in doc.paragraphs:
            if p.text.strip():
                paragraphs.append(p.text)
        
        # Also extract text from any tables in the document
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    # Deduplicate repeated text from merged cells
                    unique_cells = []
                    for c in row_cells:
                        if not unique_cells or c != unique_cells[-1]:
                            unique_cells.append(c)
                    paragraphs.append(" | ".join(unique_cells))
        
        raw_text = "\n".join(paragraphs)
        cleaned_text = normalize_extracted_text(raw_text)
        
        if not cleaned_text:
            return {
                "success": False,
                "text": "",
                "page_count": 1,
                "file_type": "DOCX",
                "is_scanned": False,
                "error": "The uploaded DOCX file contains no readable text."
            }
            
        return {
            "success": True,
            "text": cleaned_text,
            "page_count": 1,
            "file_type": "DOCX",
            "is_scanned": False,
            "error": None
        }
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "page_count": 0,
            "file_type": "DOCX",
            "is_scanned": False,
            "error": f"Failed to read DOCX file: {str(e)}"
        }


def extract_from_txt(file_path: Path) -> dict:
    """Extract text from a plain text (TXT) document."""
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    content = None
    
    for enc in encodings:
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
            
    if content is None:
        return {
            "success": False,
            "text": "",
            "page_count": 0,
            "file_type": "TXT",
            "is_scanned": False,
            "error": "Unable to decode text file with standard character encodings."
        }
        
    cleaned_text = normalize_extracted_text(content)
    if not cleaned_text:
        return {
            "success": False,
            "text": "",
            "page_count": 1,
            "file_type": "TXT",
            "is_scanned": False,
            "error": "The uploaded TXT file is empty."
        }
        
    return {
        "success": True,
        "text": cleaned_text,
        "page_count": 1,
        "file_type": "TXT",
        "is_scanned": False,
        "error": None
    }


def extract_text_from_file(file_path: str | Path) -> dict:
    """Dispatch file extraction based on file extension (.pdf, .docx, .txt)."""
    path = Path(file_path)
    if not path.exists():
        return {
            "success": False,
            "text": "",
            "page_count": 0,
            "file_type": "UNKNOWN",
            "is_scanned": False,
            "error": f"File does not exist: {path.name}"
        }
        
    ext = path.suffix.lower()
    if ext == ".pdf":
        return extract_from_pdf(path)
    elif ext == ".docx":
        return extract_from_docx(path)
    elif ext == ".txt":
        return extract_from_txt(path)
    else:
        return {
            "success": False,
            "text": "",
            "page_count": 0,
            "file_type": ext.upper().lstrip("."),
            "is_scanned": False,
            "error": f"Unsupported file extension '{ext}'. Supported types: .pdf, .docx, .txt"
        }
