
import re
from pathlib import Path

from pypdf import PdfReader


def is_heading(line: str) -> bool:
    """Identify likely headings from PDF text."""
    line = line.strip()

    if not line or len(line) > 150:
        return False

    if line.isupper() and len(line.split()) <= 15:
        return True

    if re.match(r"^(\d+(?:\.\d+)*[.)]?\s+|[A-Z][.)]\s+)", line):
        return True

    return False


def extract_pdf(pdf_path: str) -> list[dict]:
    """Extract text, page numbers and headings from a PDF."""
    path = Path(pdf_path)

    if not path.exists() or path.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(path))
    extracted_pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        headings = [line for line in lines if is_heading(line)]

        extracted_pages.append({
            "document": path.name,
            "page": page_number,
            "headings": headings,
            "text": "\n".join(lines),
        })

    return extracted_pages


def extract_folder(folder_path: str) -> list[dict]:
    """Extract all PDFs from a folder."""
    folder = Path(folder_path)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder_path}")

    all_pages = []

    for pdf_path in sorted(folder.glob("*.pdf")):
        try:
            pages = extract_pdf(str(pdf_path))
            all_pages.extend(pages)
            print(f"Processed: {pdf_path.name} ({len(pages)} pages)")
        except Exception as error:
            print(f"Failed: {pdf_path.name} - {error}")

    return all_pages


def chunk_pages(
    pages: list[dict],
    chunk_size: int = 1000,
    overlap: int = 150,
) -> list[dict]:
    """Split extracted pages into overlapping chunks."""
    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk_size or overlap")

    chunks = []

    for page_data in pages:
        text = page_data["text"].strip()

        if not text:
            continue

        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "document": page_data["document"],
                    "page": page_data["page"],
                    "headings": page_data["headings"],
                    "chunk_text": chunk_text,
                })

            if end == len(text):
                break

            start = end - overlap

    return chunks
