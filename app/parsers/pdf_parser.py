"""
app/parsers/pdf_parser.py — Extracts text and metadata from PDF files.

Library used: PyMuPDF (imported as `fitz`)
Why PyMuPDF? It's fast, accurate, and handles complex PDFs (tables, columns)
better than most alternatives like pdfplumber or PyPDF2.
"""

from pathlib import Path

import fitz  # PyMuPDF — pip package is called "pymupdf"


def extract_from_pdf(file_path: str) -> dict:
    """
    Open a PDF, read every page, and return both the raw text and metadata.

    Returns a dict with:
      - "text"     : the entire document as a single string
      - "metadata" : title, author, page count, file size, etc.
      - "pages"    : list of {page, text} so you can reference specific pages
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix}")

    # fitz.open() loads the PDF into memory
    doc = fitz.open(file_path)

    # ── Metadata ─────────────────────────────────────────────────────────────
    # doc.metadata is a dict that PDF viewers populate when a file is saved.
    # Many PDFs leave these blank — that's fine, we default to "Unknown".
    metadata = {
        "title": doc.metadata.get("title", "Unknown"),
        "author": doc.metadata.get("author", "Unknown"),
        "subject": doc.metadata.get("subject", ""),
        "creator": doc.metadata.get("creator", ""),  # app used to create
        "producer": doc.metadata.get("producer", ""),  # PDF library used
        "creation_date": doc.metadata.get("creationDate", ""),
        "modification_date": doc.metadata.get("modDate", ""),
        "page_count": doc.page_count,
        "file_name": path.name,
        "file_size_kb": round(path.stat().st_size / 1024, 2),
        "file_type": "PDF",
    }

    # ── Text Extraction ───────────────────────────────────────────────────────
    # We iterate page by page. page.get_text() returns plain text for that page.
    # Keeping per-page data lets us later cite which page an answer came from.
    pages_text = []
    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text().strip()
        pages_text.append({"page": page_num + 1, "text": text})

    # Join all page texts with double newlines to preserve document structure
    full_text = "\n\n".join(p["text"] for p in pages_text if p["text"])

    doc.close()  # Always close the file handle when done

    return {
        "text": full_text,
        "metadata": metadata,
        "pages": pages_text,
    }
