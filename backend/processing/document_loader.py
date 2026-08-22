from pathlib import Path
from pypdf import PdfReader


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from all pages of a PDF.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    reader = PdfReader(path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)