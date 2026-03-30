"""
File loaders for the RAG pipeline.
Supports: .txt, .md, .pdf, .docx, .csv
"""
import csv
import io
from pathlib import Path
from typing import Optional


def load_text(file_path: str) -> str:
    """Load plain text or markdown files."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()


def load_pdf(file_path: str) -> str:
    """Load PDF files using PyPDF2."""
    from PyPDF2 import PdfReader

    reader = PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return '\n\n'.join(pages)


def load_docx(file_path: str) -> str:
    """Load .docx files using python-docx."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return '\n\n'.join(paragraphs)


def load_csv(file_path: str) -> str:
    """
    Load .csv files and convert to a readable text representation.
    Each row becomes a line with 'column: value' pairs.
    """
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        reader = csv.DictReader(f)
        rows = []
        for i, row in enumerate(reader):
            line = ' | '.join(f"{k}: {v}" for k, v in row.items() if v)
            rows.append(f"Row {i + 1}: {line}")
            if i >= 5000:  # Safety cap for very large CSVs
                rows.append(f"... (truncated after {i + 1} rows)")
                break
        return '\n'.join(rows)


# Map file extensions to their loader functions
LOADERS = {
    '.txt': load_text,
    '.md': load_text,
    '.pdf': load_pdf,
    '.docx': load_docx,
    '.csv': load_csv,
}

SUPPORTED_EXTENSIONS = set(LOADERS.keys())


def load_file(file_path: str) -> Optional[str]:
    """
    Load a file and return its text content.
    Returns None if the file type is not supported.
    """
    ext = Path(file_path).suffix.lower()
    loader = LOADERS.get(ext)
    if loader is None:
        return None
    return loader(file_path)
