from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class KnowledgeChunk:
    """
    Representation of a processed knowledge chunk with metadata.
    """
    chunk_id: int
    text: str
    source: str
    section: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "source": self.source,
            "section": self.section,
        }


class KnowledgeStore:
    """
    In-memory registry of structured knowledge chunks.
    Preserves text content and metadata for downstream embeddings and FAISS.
    """

    def __init__(self) -> None:
        self.chunks: List[KnowledgeChunk] = []

    def add_chunk(
        self,
        chunk_id: int,
        text: str,
        source: str,
        section: str,
    ) -> KnowledgeChunk:
        """
        Add a single chunk to the store.
        """
        chunk = KnowledgeChunk(
            chunk_id=chunk_id,
            text=text,
            source=source,
            section=section,
        )
        self.chunks.append(chunk)
        return chunk

    def add_from_dicts(
        self,
        raw_chunks: List[Dict[str, Any]],
        start_id: Optional[int] = None,
    ) -> List[KnowledgeChunk]:
        """
        Converts raw chunk dictionaries from processing/chunker.py into KnowledgeChunks
        with integer chunk_ids, preserving source, section, and text.
        """
        added: List[KnowledgeChunk] = []
        base_id = len(self.chunks) if start_id is None else start_id

        for idx, rc in enumerate(raw_chunks):
            text = rc.get("text") or rc.get("content", "")
            source = rc.get("source", "resume")
            section = rc.get("section", "General")
            chunk_id = base_id + idx

            chunk = self.add_chunk(
                chunk_id=chunk_id,
                text=text,
                source=source,
                section=section,
            )
            added.append(chunk)

        return added

    def get_texts(self) -> List[str]:
        """
        Get all chunk texts for embedding generation.
        """
        return [chunk.text for chunk in self.chunks]

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """
        Export all chunks as dictionaries.
        """
        return [chunk.to_dict() for chunk in self.chunks]

    def clear(self) -> None:
        """
        Clear all stored chunks.
        """
        self.chunks.clear()

    def __len__(self) -> int:
        return len(self.chunks)

    def __getitem__(self, index: int) -> KnowledgeChunk:
        return self.chunks[index]
