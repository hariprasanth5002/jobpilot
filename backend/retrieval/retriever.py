import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from knowledge.embedding import EmbeddingService, DEFAULT_MODEL_NAME, normalize_embeddings
from knowledge.vector_store import VectorStore, DEFAULT_STORAGE_DIR
from retrieval.query_understanding import understand_query, QueryUnderstandingResult


@dataclass
class RetrievedChunk:
    """
    Representation of a single retrieved knowledge chunk.
    """
    rank: int
    chunk_id: int
    faiss_id: int
    text: str
    source: str
    section: str
    distance: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "chunk_id": self.chunk_id,
            "faiss_id": self.faiss_id,
            "text": self.text,
            "source": self.source,
            "section": self.section,
            "distance": round(self.distance, 6),
        }


@dataclass
class RetrievalResponse:
    """
    Complete structured retrieval response.
    """
    question: str
    intent: str
    retrieval_strategy: List[str]
    results: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "intent": self.intent,
            "retrieval_strategy": self.retrieval_strategy,
            "results": self.results,
        }


class Retriever:
    """
    Orchestrates Query Understanding -> Query Embedding -> L2 Normalization
    -> FAISS Search -> Metadata Mapping -> Source Prioritization.
    """

    _instance: Optional["Retriever"] = None

    def __init__(
        self,
        storage_dir: str = DEFAULT_STORAGE_DIR,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> None:
        self.storage_dir = storage_dir
        self.model_name = model_name
        self.embedding_service = EmbeddingService.get_instance(model_name)
        self.vector_store: Optional[VectorStore] = None
        self._ensure_vector_store()

    def _resolve_storage_dir(self) -> str:
        """
        Locates the knowledge_base directory whether executed from backend/ or project root.
        """
        candidates = [
            self.storage_dir,
            os.path.join("backend", self.storage_dir),
            os.path.join("..", self.storage_dir),
        ]
        for c in candidates:
            if os.path.exists(os.path.join(c, "index.faiss")) and os.path.exists(
                os.path.join(c, "chunks.json")
            ):
                return c
        return self.storage_dir

    def _ensure_vector_store(self) -> VectorStore:
        """
        Load FAISS index and chunk metadata into memory if not already loaded.
        """
        if self.vector_store is None:
            resolved_dir = self._resolve_storage_dir()
            store = VectorStore()
            store.load_index(storage_dir=resolved_dir)
            self.vector_store = store
        return self.vector_store

    def retrieve(
        self,
        question: str,
        top_k: int = 5,
    ) -> RetrievalResponse:
        """
        Execute full deterministic retrieval pipeline for a given user question.

        1. Input validation
        2. Query understanding (intent & source priority strategy)
        3. Query embedding & L2 normalization
        4. FAISS IndexFlatL2 search for candidate pool
        5. Metadata lookup from chunks.json
        6. Source prioritization reranking
        7. Top-K chunk assembly
        """
        clean_question = question.strip() if question else ""

        # 1. Query Understanding
        understanding: QueryUnderstandingResult = understand_query(clean_question)
        intent = understanding.intent
        retrieval_strategy = understanding.retrieval_strategy

        # Handle empty/invalid query safely
        if not clean_question:
            return RetrievalResponse(
                question="",
                intent=intent,
                retrieval_strategy=retrieval_strategy,
                results=[],
            )

        # 2. Vector Store & Candidates Search
        store = self._ensure_vector_store()
        total_vectors = store.total_vectors
        if total_vectors == 0:
            return RetrievalResponse(
                question=clean_question,
                intent=intent,
                retrieval_strategy=retrieval_strategy,
                results=[],
            )

        # 3. Query Embedding + L2 Normalization
        # Embed single query
        raw_embedding = self.embedding_service.encode([clean_question], normalize=False)
        query_vector = normalize_embeddings(raw_embedding)

        # 4. Search FAISS index for candidate pool
        # Retrieve a broader candidate pool to allow source prioritization
        candidate_k = min(total_vectors, max(top_k * 3, 10))
        faiss_ids, distances = store.search(query_vector, k=candidate_k)

        # -------------------------------------------------------------------
        # DEBUG: RETRIEVAL LOGGING
        # -------------------------------------------------------------------
        print()
        print("============================================================")
        print("JOBPILOT RETRIEVAL")
        print("============================================================")
        print(f"Query    : {clean_question}")
        print(f"Intent   : {intent}")
        print(f"Strategy : {retrieval_strategy}")
        print(f"")
        print(f"FAISS IndexFlatL2: returns {candidate_k} nearest neighbours.")
        print(f"Lower L2 distance = greater semantic similarity.")
        print(f"Total vectors in index: {total_vectors}")
        print()

        # 5. Metadata lookup & candidate preparation
        candidates: List[Dict[str, Any]] = []
        for fid, dist in zip(faiss_ids, distances):
            chunk_meta = store.get_chunk(fid)
            if chunk_meta is None:
                raise KeyError(f"FAISS ID {fid} cannot be mapped to chunk metadata in chunks.json!")

            candidates.append({
                "faiss_id": fid,
                "chunk_id": int(chunk_meta.get("chunk_id", fid)),
                "text": str(chunk_meta.get("text", "")),
                "source": str(chunk_meta.get("source", "")),
                "section": str(chunk_meta.get("section", "")),
                "distance": float(dist),
            })

        # 6. Apply Source Prioritization
        # Build priority weight map based on retrieval_strategy order
        # Primary source -> tier 0, Secondary -> tier 1, etc.
        source_priority_map: Dict[str, int] = {
            src.lower(): idx for idx, src in enumerate(retrieval_strategy)
        }
        fallback_priority = len(retrieval_strategy)

        def ranking_key(item: Dict[str, Any]) -> float:
            src = item["source"].lower()
            priority_rank = source_priority_map.get(src, fallback_priority)
            return item["distance"] * (1.0 + 0.15 * priority_rank)

        # Sort candidates using source prioritization
        prioritized_candidates = sorted(candidates, key=ranking_key)

        # -------------------------------------------------------------------
        # DEBUG: TOP-K RESULTS LOGGING
        # -------------------------------------------------------------------
        print(f"Top-{top_k} Results after Source Prioritization Reranking:")
        print("------------------------------------------------------------")

        # 7. Select Top-K and build result models
        final_results: List[Dict[str, Any]] = []
        for rank, item in enumerate(prioritized_candidates[:top_k], start=1):
            retrieved_chunk = RetrievedChunk(
                rank=rank,
                chunk_id=item["chunk_id"],
                faiss_id=item["faiss_id"],
                text=item["text"],
                source=item["source"],
                section=item["section"],
                distance=item["distance"],
            )
            final_results.append(retrieved_chunk.to_dict())
            print(f"Rank     : {rank}")
            print(f"FAISS ID : {item['faiss_id']}")
            print(f"Chunk ID : {item['chunk_id']}")
            print(f"Distance : {item['distance']:.6f}")
            print(f"Source   : {item['source']}")
            print(f"Section  : {item['section']}")
            text_preview = item['text'].replace('\n', ' ').strip()
            safe_preview = text_preview[:200].encode('ascii', errors='replace').decode('ascii')
            print(f"Text     : {safe_preview}{'...' if len(text_preview) > 200 else ''}")
            print()

        print(f"Total retrieved chunks: {len(final_results)}")
        print("============================================================")
        print()

        return RetrievalResponse(
            question=clean_question,
            intent=intent,
            retrieval_strategy=retrieval_strategy,
            results=final_results,
        )


# Top-level helper function
def retrieve(
    question: str,
    top_k: int = 5,
    storage_dir: str = DEFAULT_STORAGE_DIR,
) -> Dict[str, Any]:
    """
    Main retrieval entry point.
    """
    retriever = Retriever(storage_dir=storage_dir)
    response = retriever.retrieve(question=question, top_k=top_k)
    return response.to_dict()
