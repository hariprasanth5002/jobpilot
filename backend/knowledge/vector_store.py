import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import faiss
import numpy as np

from knowledge.knowledge_store import KnowledgeChunk, KnowledgeStore

DEFAULT_STORAGE_DIR = "knowledge_base"
DEFAULT_INDEX_FILENAME = "index.faiss"
DEFAULT_CHUNKS_FILENAME = "chunks.json"


class VectorStore:
    """
    FAISS IndexFlatL2 vector index manager with metadata persistence.
    Maintains 1:1 mapping between FAISS vector IDs and KnowledgeChunk metadata.
    """

    def __init__(self, dimension: Optional[int] = None) -> None:
        self.dimension: Optional[int] = dimension
        self.index: Optional[faiss.IndexFlatL2] = None
        self.chunks: List[Dict[str, Any]] = []

    def build_index(
        self,
        embeddings: np.ndarray,
        chunks: Union[List[Dict[str, Any]], List[KnowledgeChunk], KnowledgeStore],
    ) -> faiss.IndexFlatL2:
        """
        Build an IndexFlatL2 FAISS index and associate chunk metadata.

        Args:
            embeddings: Normalized float32 numpy array of shape (N, D).
            chunks: List of chunk dicts, KnowledgeChunks, or KnowledgeStore.
        """
        if embeddings.ndim != 2:
            raise ValueError(f"Embeddings must be 2D array, got shape {embeddings.shape}")

        num_vectors, dim = embeddings.shape
        self.dimension = dim

        # Normalize chunk metadata to standard list of dicts
        normalized_chunks: List[Dict[str, Any]] = []
        if isinstance(chunks, KnowledgeStore):
            normalized_chunks = chunks.to_dict_list()
        elif isinstance(chunks, list):
            for idx, c in enumerate(chunks):
                if isinstance(c, KnowledgeChunk):
                    normalized_chunks.append(c.to_dict())
                elif isinstance(c, dict):
                    # Ensure chunk_id is present and integer
                    chunk_dict = {
                        "chunk_id": int(c.get("chunk_id", idx)),
                        "text": str(c.get("text") or c.get("content", "")),
                        "source": str(c.get("source", "general")),
                        "section": str(c.get("section", "General")),
                    }
                    normalized_chunks.append(chunk_dict)
                else:
                    raise TypeError(f"Unsupported chunk type: {type(c)}")

        if num_vectors != len(normalized_chunks):
            raise ValueError(
                f"Mismatch: {num_vectors} vectors but {len(normalized_chunks)} chunks provided."
            )

        # Initialize FAISS IndexFlatL2
        self.index = faiss.IndexFlatL2(self.dimension)

        # Ensure float32 format
        vectors = embeddings.astype(np.float32)

        # Add vectors to index (assigned IDs 0 to N-1 sequentially)
        self.index.add(vectors)
        self.chunks = normalized_chunks

        return self.index

    def save_index(
        self,
        storage_dir: str = DEFAULT_STORAGE_DIR,
        index_filename: str = DEFAULT_INDEX_FILENAME,
        chunks_filename: str = DEFAULT_CHUNKS_FILENAME,
    ) -> Tuple[str, str]:
        """
        Save FAISS index and chunk metadata to disk.
        """
        if self.index is None:
            raise ValueError("No FAISS index to save. Build or load an index first.")

        os.makedirs(storage_dir, exist_ok=True)

        index_path = os.path.join(storage_dir, index_filename)
        chunks_path = os.path.join(storage_dir, chunks_filename)

        # 1. Save FAISS index
        faiss.write_index(self.index, index_path)

        # 2. Save chunk metadata (excluding embeddings)
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, indent=2, ensure_ascii=False)

        return index_path, chunks_path

    def load_index(
        self,
        storage_dir: str = DEFAULT_STORAGE_DIR,
        index_filename: str = DEFAULT_INDEX_FILENAME,
        chunks_filename: str = DEFAULT_CHUNKS_FILENAME,
    ) -> "VectorStore":
        """
        Load an existing FAISS index and chunk metadata from disk.
        """
        index_path = os.path.join(storage_dir, index_filename)
        chunks_path = os.path.join(storage_dir, chunks_filename)

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index file not found at: {index_path}")
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks metadata file not found at: {chunks_path}")

        # 1. Read FAISS index
        self.index = faiss.read_index(index_path)
        self.dimension = self.index.d

        # 2. Read chunk metadata
        with open(chunks_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        return self

    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
    ) -> Tuple[List[int], List[float]]:
        """
        Search the FAISS index with a normalized query vector.

        Args:
            query_vector: 1D (D,) or 2D (1, D) normalized numpy array.
            k: Number of nearest neighbors to retrieve.

        Returns:
            Tuple of (faiss_ids, l2_distances).
        """
        if self.index is None:
            raise ValueError("FAISS index is not initialized. Build or load an index first.")

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        query_vector = query_vector.astype(np.float32)

        k = min(k, self.index.ntotal)
        distances, indices = self.index.search(query_vector, k)

        faiss_ids: List[int] = indices[0].tolist()
        l2_distances: List[float] = distances[0].tolist()

        return faiss_ids, l2_distances

    def get_chunk(self, faiss_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve chunk metadata corresponding to a FAISS vector ID.
        """
        if 0 <= faiss_id < len(self.chunks):
            return self.chunks[faiss_id]
        return None

    def search_with_metadata(
        self,
        query_vector: np.ndarray,
        k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search FAISS index and return ranked results with enriched chunk metadata.
        """
        faiss_ids, distances = self.search(query_vector, k=k)
        results: List[Dict[str, Any]] = []

        for rank, (fid, dist) in enumerate(zip(faiss_ids, distances), start=1):
            chunk_data = self.get_chunk(fid)
            if chunk_data:
                results.append({
                    "rank": rank,
                    "faiss_id": fid,
                    "l2_distance": dist,
                    "chunk_id": chunk_data.get("chunk_id", fid),
                    "source": chunk_data.get("source", ""),
                    "section": chunk_data.get("section", ""),
                    "text": chunk_data.get("text", ""),
                })

        return results

    @property
    def total_vectors(self) -> int:
        return self.index.ntotal if self.index is not None else 0

    @property
    def index_type(self) -> str:
        return type(self.index).__name__ if self.index is not None else "None"


# --- Standalone convenience functions ---


def build_index(
    embeddings: np.ndarray,
    chunks: Union[List[Dict[str, Any]], List[KnowledgeChunk], KnowledgeStore],
) -> VectorStore:
    store = VectorStore()
    store.build_index(embeddings, chunks)
    return store


def save_index(
    store: VectorStore,
    storage_dir: str = DEFAULT_STORAGE_DIR,
) -> Tuple[str, str]:
    return store.save_index(storage_dir=storage_dir)


def load_index(
    storage_dir: str = DEFAULT_STORAGE_DIR,
) -> VectorStore:
    store = VectorStore()
    store.load_index(storage_dir=storage_dir)
    return store


def search(
    store: VectorStore,
    query_vector: np.ndarray,
    k: int = 5,
) -> Tuple[List[int], List[float]]:
    return store.search(query_vector=query_vector, k=k)
