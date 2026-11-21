"""
DOCX parser for extracting screenplay text.
"""
from pathlib import Path
from app.utils.logging import logger

try:
    import docx
except ImportError:
    docx = None


def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text paragraphs and tables from a DOCX file."""
    if docx is None:
        raise ImportError("python-docx is required to extract text from DOCX files.")
    
    text_parts = []
    try:
        doc = docx.Document(str(file_path))
        for paragraph in doc.paragraphs:
            if paragraph.text:
                text_parts.append(paragraph.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)
        return "\n".join(text_parts)
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX {file_path}: {e}")
        raise ValueError(f"Could not parse DOCX file {file_path.name}: {e}")
