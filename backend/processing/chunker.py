import re
from typing import Any, Dict, List, Optional
from processing.cleaner import clean_text
from processing.section_detector import detect_sections


def _split_text_with_overlap(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[str]:
    """
    Split a large text block into chunks by paragraphs/sentences with overlap,
    avoiding blind character slicing.
    """
    if len(text) <= chunk_size:
        return [text]

    # Split into paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # If single block without paragraph breaks, split by lines or sentences
    units: List[str] = []
    for para in paragraphs:
        if len(para) > chunk_size:
            # Split paragraph into sentences or bullet points
            sentences = re.split(r"(?<=[.!?])\s+|\n", para)
            for s in sentences:
                s_clean = s.strip()
                if s_clean:
                    units.append(s_clean)
        else:
            units.append(para)

    chunks: List[str] = []
    current_chunk: List[str] = []
    current_length = 0

    for unit in units:
        unit_len = len(unit)

        # If a single unit itself exceeds chunk_size, split by words
        if unit_len > chunk_size:
            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())
                current_chunk = []
                current_length = 0

            words = unit.split(" ")
            word_chunk: List[str] = []
            word_len = 0

            for word in words:
                if word_len + len(word) + 1 > chunk_size and word_chunk:
                    chunks.append(" ".join(word_chunk).strip())
                    # Overlap: retain trailing words for overlap
                    overlap_words: List[str] = []
                    overlap_len = 0
                    for w in reversed(word_chunk):
                        if overlap_len + len(w) + 1 <= chunk_overlap:
                            overlap_words.insert(0, w)
                            overlap_len += len(w) + 1
                        else:
                            break
                    word_chunk = overlap_words + [word]
                    word_len = sum(len(w) + 1 for w in word_chunk)
                else:
                    word_chunk.append(word)
                    word_len += len(word) + 1

            if word_chunk:
                chunks.append(" ".join(word_chunk).strip())
            continue

        if current_length + unit_len + 1 > chunk_size and current_chunk:
            chunk_str = "\n".join(current_chunk).strip()
            chunks.append(chunk_str)

            # Build overlap context from previous units
            overlap_units: List[str] = []
            overlap_len = 0
            for u in reversed(current_chunk):
                if overlap_len + len(u) + 1 <= chunk_overlap:
                    overlap_units.insert(0, u)
                    overlap_len += len(u) + 1
                else:
                    break

            current_chunk = overlap_units + [unit]
            current_length = sum(len(u) + 1 for u in current_chunk)
        else:
            current_chunk.append(unit)
            current_length += unit_len + 1

    if current_chunk:
        final_str = "\n".join(current_chunk).strip()
        if not chunks or final_str != chunks[-1]:
            chunks.append(final_str)

    return chunks if chunks else [text]


def chunk_sections(
    sections: Dict[str, str],
    source: str = "resume",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Generate section-aware chunks from segmented sections.

    Each chunk contains:
    - chunk_id: Unique identifier for the chunk
    - source: 'resume', 'job_description', or 'user_details'
    - section: Section name
    - content: Chunk text content
    """
    valid_sources = {"resume", "job_description", "user_details"}
    normalized_source = source.lower().replace(" ", "_")
    if normalized_source not in valid_sources:
        # Fallback to provided source if custom
        normalized_source = source

    chunks: List[Dict[str, Any]] = []
    chunk_index = 0

    for section_name, section_text in sections.items():
        if not section_text or not section_text.strip():
            continue

        section_chunks = _split_text_with_overlap(
            section_text.strip(),
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for sc in section_chunks:
            if not sc.strip():
                continue
            chunk_dict = {
                "chunk_id": f"{normalized_source}_{chunk_index}",
                "source": normalized_source,
                "section": section_name,
                "content": sc.strip(),
            }
            chunks.append(chunk_dict)
            chunk_index += 1

    return chunks


def chunk_document(
    text: str,
    source: str = "resume",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    End-to-end convenience function to clean, segment, and chunk a document.
    """
    cleaned = clean_text(text)
    sections = detect_sections(cleaned)
    return chunk_sections(
        sections=sections,
        source=source,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
