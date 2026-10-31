"""
Document Loader and Preprocessing for RAG.
Extracts text and page metadata from PDF documents using pypdf.
"""

import re
import logging
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader

logger = logging.getLogger("rag.document_loader")


def clean_text(text: str) -> str:
    """Clean and normalize extracted PDF text."""
    if not text:
        return ""
    # Normalize unicode whitespace
    text = re.sub(r"[\r\t\f\v]+", " ", text)
    # Replace multiple consecutive spaces
    text = re.sub(r" +", " ", text)
    # Fix hyphenated words broken across line wraps
    text = re.sub(r"(\w+)-\s*\n\s*(\w+)", r"\1\2", text)
    # Normalize multiple newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def load_pdf_document(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extracts text page-by-page from a PDF file.
    Returns list of page documents with page numbers and cleaned text.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF document not found at: {path}")

    logger.info(f"Loading PDF document from: {path}")
    pages_data = []

    try:
        reader = PdfReader(str(path))
        num_pages = len(reader.pages)
        logger.info(f"PDF has {num_pages} pages.")

        for page_idx, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            cleaned = clean_text(raw_text)
            if cleaned:
                pages_data.append({
                    "text": cleaned,
                    "metadata": {
                        "source": path.name,
                        "file_path": str(path),
                        "page_number": page_idx,
                        "total_pages": num_pages,
                    }
                })

        return pages_data
    except Exception as e:
        logger.error(f"Error extracting text from PDF {path}: {e}", exc_info=True)
        raise
