import re


def clean_text(text: str) -> str:
    """
    Clean and normalize raw extracted document text.

    Operations:
    - Normalizes line endings to \\n.
    - Replaces non-breaking and zero-width spaces.
    - Trims trailing/leading whitespace per line and collapses redundant inline spaces.
    - Collapses 3+ consecutive newlines down to 2 newlines (paragraph boundary).
    - Preserves bullet points, punctuation, casing, and document structure.
    - Does not use an LLM.
    """
    if not text:
        return ""

    # 1. Normalize line endings (CRLF / CR -> LF)
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2. Normalize special unicode spaces and zero-width characters
    cleaned = cleaned.replace("\u00a0", " ")
    cleaned = cleaned.replace("\u200b", "")
    cleaned = cleaned.replace("\ufeff", "")

    # 3. Process line by line: remove excessive spaces/tabs within lines
    lines = []
    for line in cleaned.split("\n"):
        # Replace multiple horizontal whitespaces (spaces/tabs) with a single space
        line = re.sub(r"[ \t]+", " ", line)
        lines.append(line.strip())

    cleaned = "\n".join(lines)

    # 4. Collapse 3+ consecutive newlines into 2 (preserves empty line paragraph breaks)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # 5. Trim leading and trailing whitespace of the entire document
    return cleaned.strip()
