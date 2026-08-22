"""
JobPilot Pipeline Orchestrator
-------------------------------
Thin service layer that wires together the existing RAG modules.
FastAPI routes call run_pipeline() — no RAG logic lives here.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from processing.document_loader import extract_pdf_text
from processing.chunker import chunk_document
from knowledge.knowledge_store import KnowledgeStore
from knowledge.embedding import EmbeddingService, DEFAULT_MODEL_NAME
from knowledge.vector_store import VectorStore, DEFAULT_STORAGE_DIR
from retrieval.retriever import Retriever, RetrievalResponse
from generation.context_builder import build_context
from generation.guardrails import validate_context
from generation.llm import generate_answer, OllamaClient

# ---------------------------------------------------------------------------
# Relevance filter
# ---------------------------------------------------------------------------
# FAISS IndexFlatL2 always returns k nearest neighbours even for irrelevant
# queries. Any chunk whose L2 distance exceeds this threshold is discarded.
# Calibrated against verified test queries:
#   - Agri Notifier (highly relevant): 1.023
#   - AWS / SKILL_GAP queries:         0.79 – 1.76
#   - Completely off-topic queries:    typically > 1.85
RELEVANCE_THRESHOLD: float = float(os.environ.get("JOBPILOT_RELEVANCE_THRESHOLD", "1.30"))

# --- Paths ---
BACKEND_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BACKEND_DIR / "uploads"
KNOWLEDGE_BASE_DIR = BACKEND_DIR / "knowledge_base"

# Ensure upload directory exists at import time
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Module-level singletons – loaded once per process
_retriever: Optional[Retriever] = None
_ollama_client: Optional[OllamaClient] = None


def _get_retriever(force_reload: bool = False) -> Retriever:
    """Return the cached Retriever, reloading if the knowledge base was updated."""
    global _retriever
    if _retriever is None or force_reload:
        _retriever = Retriever(storage_dir=str(KNOWLEDGE_BASE_DIR))
    return _retriever


def _get_ollama_client() -> OllamaClient:
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client


# ---------------------------------------------------------------------------
# Document Ingestion Pipeline
# ---------------------------------------------------------------------------

def ingest_document(file_path: str, source: str) -> Dict[str, Any]:
    """
    Run the full document ingestion pipeline for a single file.

    PDF → extract → clean → section-detect → chunk → embed → FAISS → save

    Args:
        file_path: Absolute path to the uploaded PDF.
        source:    'resume', 'job_description', or 'user_details'.

    Returns:
        Dict with statistics about the ingestion result.
    """
    # 1. Extract text from PDF
    raw_text = extract_pdf_text(file_path)
    if not raw_text.strip():
        raise ValueError(f"No extractable text found in uploaded PDF: {file_path}")

    # 2. Chunk through existing processing pipeline (clean + detect sections + chunk)
    new_chunks = chunk_document(raw_text, source=source)
    if not new_chunks:
        raise ValueError(f"Document produced no usable chunks after processing.")

    # 3. Load existing chunks from knowledge_base (to merge, not replace)
    existing_store = KnowledgeStore()
    existing_chunks_path = KNOWLEDGE_BASE_DIR / "chunks.json"

    if existing_chunks_path.exists():
        import json
        with open(existing_chunks_path, "r", encoding="utf-8") as f:
            existing_raw = json.load(f)
        # Filter out chunks from the same source (replace them with fresh ones)
        kept_chunks = [c for c in existing_raw if c.get("source") != source]
    else:
        kept_chunks = []

    # 4. Merge kept chunks with the new ones into a KnowledgeStore
    all_raw_chunks = kept_chunks + new_chunks
    # Re-index chunk_ids sequentially so FAISS position == chunk_id
    for idx, chunk in enumerate(all_raw_chunks):
        chunk["chunk_id"] = idx

    merged_store = KnowledgeStore()
    merged_store.add_from_dicts(all_raw_chunks)

    # 5. Generate embeddings for all merged chunks
    embedding_service = EmbeddingService.get_instance(DEFAULT_MODEL_NAME)
    texts = merged_store.get_texts()
    embeddings = embedding_service.encode(texts, normalize=True)

    # 6. Build and save FAISS index
    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    vector_store = VectorStore()
    vector_store.build_index(embeddings, merged_store)
    vector_store.save_index(storage_dir=str(KNOWLEDGE_BASE_DIR))

    # 7. Force retriever singleton to reload with the new index on next call
    global _retriever
    _retriever = None

    return {
        "source": source,
        "new_chunks": len(new_chunks),
        "total_chunks": len(merged_store),
        "vectors_indexed": vector_store.total_vectors,
    }


def ingest_user_details(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert structured user details dict into a text chunk and ingest into FAISS.

    Args:
        user_data: Dict with keys target_role, skills, projects, experience,
                   education, career_goals.

    Returns:
        Dict with ingestion statistics.
    """
    lines = []
    if user_data.get("target_role"):
        lines.append(f"Target Role: {user_data['target_role']}")
    if user_data.get("experience"):
        lines.append(f"Years of Experience: {user_data['experience']}")
    if user_data.get("skills"):
        lines.append(f"Key Skills: {user_data['skills']}")
    if user_data.get("projects"):
        lines.append(f"Notable Projects: {user_data['projects']}")
    if user_data.get("education"):
        lines.append(f"Education: {user_data['education']}")
    if user_data.get("career_goals"):
        lines.append(f"Career Goals: {user_data['career_goals']}")

    if not lines:
        raise ValueError("User details are empty — at least target_role is required.")

    text = "\n".join(lines)

    # Build a single chunk for user details
    new_chunks = [{
        "chunk_id": 0,
        "source": "user_details",
        "section": "General",
        "content": text,
        "text": text,
    }]

    # Merge with existing knowledge base, replacing previous user_details
    import json
    existing_chunks_path = KNOWLEDGE_BASE_DIR / "chunks.json"
    if existing_chunks_path.exists():
        with open(existing_chunks_path, "r", encoding="utf-8") as f:
            existing_raw = json.load(f)
        kept_chunks = [c for c in existing_raw if c.get("source") != "user_details"]
    else:
        kept_chunks = []

    all_raw_chunks = kept_chunks + new_chunks
    for idx, chunk in enumerate(all_raw_chunks):
        chunk["chunk_id"] = idx

    merged_store = KnowledgeStore()
    merged_store.add_from_dicts(all_raw_chunks)

    embedding_service = EmbeddingService.get_instance(DEFAULT_MODEL_NAME)
    texts = merged_store.get_texts()
    embeddings = embedding_service.encode(texts, normalize=True)

    KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    vector_store = VectorStore()
    vector_store.build_index(embeddings, merged_store)
    vector_store.save_index(storage_dir=str(KNOWLEDGE_BASE_DIR))

    global _retriever
    _retriever = None

    return {
        "source": "user_details",
        "new_chunks": len(new_chunks),
        "total_chunks": len(merged_store),
        "vectors_indexed": vector_store.total_vectors,
    }


# ---------------------------------------------------------------------------
# Chat Pipeline
# ---------------------------------------------------------------------------

def run_pipeline(question: str) -> Dict[str, Any]:
    """
    Execute the complete RAG pipeline for a user question.

    question
        → Retriever (query_understanding → embedding → FAISS → rerank)
        → build_context
        → validate_context (guardrails)
        → generate_answer (Ollama — skipped if guardrail blocks)
        → structured JSON response

    Returns:
        {
            "question":  str,
            "intent":    str,
            "answer":    str,
            "sources":   List[{chunk_id, source, section}],
            "guardrail_blocked": bool,
        }
    """
    clean_question = question.strip() if question else ""

    # 1. Retrieve relevant chunks
    retriever = _get_retriever()
    retrieval_response = retriever.retrieve(clean_question, top_k=5)

    # 2. Relevance filter — if the BEST matching chunk's L2 distance exceeds
    # the threshold the entire query is treated as off-topic and we return no
    # context, letting the guardrail block the LLM call gracefully.
    # FAISS IndexFlatL2 always returns k neighbours regardless of relevance;
    # this guard prevents "nearest garbage" from slipping through.
    #
    # Calibration (all-MiniLM-L6-v2, current KB):
    #   Legitimate query best distances:  0.79 – 1.30
    #   Off-topic passphrase best dist:   1.36  →  correctly blocked
    if retrieval_response.results:
        best_distance = min(r.get("distance", 999.0) for r in retrieval_response.results)
        if best_distance > RELEVANCE_THRESHOLD:
            retrieval_response = RetrievalResponse(
                question=retrieval_response.question,
                intent=retrieval_response.intent,
                retrieval_strategy=retrieval_response.retrieval_strategy,
                results=[],
            )

    # 3. Build structured context from (filtered) retrieval results
    context = build_context(
        question=clean_question,
        retrieval_result=retrieval_response,
    )

    # 4. Guardrail validation
    guardrail_result = validate_context(context)

    # 5. Generate answer (or safe fallback if blocked by guardrail)
    client = _get_ollama_client()
    generation_result = generate_answer(
        question=clean_question,
        intent=retrieval_response.intent,
        validated_guardrail_result=guardrail_result,
        client=client,
    )

    # 6. Build source attribution list — empty if guardrail blocked
    if generation_result["allowed"]:
        all_retrieved = (
            context.resume + context.job_description + context.user_details
        )
        sources: List[Dict[str, Any]] = [
            {
                "chunk_id": c["chunk_id"],
                "source": c["source"],
                "section": c["section"],
            }
            for c in all_retrieved
        ]
    else:
        sources = []

    return {
        "question": clean_question,
        "intent": generation_result["intent"],
        "answer": generation_result["answer"],
        "sources": sources,
        "guardrail_blocked": not generation_result["allowed"],
    }
