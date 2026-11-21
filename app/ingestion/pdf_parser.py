"""
PDF parser for extracting screenplay text.
"""
from pathlib import Path
from typing import Optional
from app.utils.logging import logger

try:
    import pypdf
except ImportError:
    pypdf = None


def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts plain text from a PDF file using pypdf."""
    if pypdf is None:
        raise ImportError("pypdf is required to extract text from PDF files.")
    
    text_content = []
    try:
        reader = pypdf.PdfReader(str(file_path))
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
        return "\n\n".join(text_content)
    except Exception as e:
        logger.error(f"Failed to extract text from PDF {file_path}: {e}")
        raise ValueError(f"Could not parse PDF file {file_path.name}: {e}")
