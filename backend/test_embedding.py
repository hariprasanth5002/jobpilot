import os
import numpy as np

from processing.document_loader import extract_pdf_text
from processing.cleaner import clean_text
from processing.section_detector import detect_sections
from processing.chunker import chunk_sections, chunk_document
from knowledge.knowledge_store import KnowledgeStore
from knowledge.embedding import (
    EmbeddingService,
    generate_embeddings,
    normalize_embeddings,
    DEFAULT_MODEL_NAME,
)


def main():
    print("=" * 70)
    print("JOBPILOT: EMBEDDING LAYER TEST")
    print("=" * 70)

    # 1. Load Chunks from Existing Processing Pipeline
    print("\n[1] Generating chunks from processing pipeline...")

    # Load Resume PDF
    sample_pdf_path = "sample_resume.pdf"
    if not os.path.exists(sample_pdf_path):
        from test_processing import create_sample_resume_pdf
        create_sample_resume_pdf(sample_pdf_path)

    raw_pdf_text = extract_pdf_text(sample_pdf_path)
    cleaned_pdf_text = clean_text(raw_pdf_text)
    resume_sections = detect_sections(cleaned_pdf_text)
    raw_resume_chunks = chunk_sections(resume_sections, source="resume", chunk_size=300, chunk_overlap=30)

    # Job Description Chunks
    sample_jd = """
    About the Role
    We are looking for a Senior AI & Backend Engineer to build high-performance retrieval pipelines and integrate local LLMs for structured query processing.

    Responsibilities
    - Design and develop scalable FastAPI services for document parsing and FAISS vector indexing.
    - Implement robust section detection and chunking algorithms.
    - Integrate Ollama LLMs with strict guardrails and prompt templates.

    Requirements
    - 4+ years of professional backend engineering experience in Python.
    - Hands-on experience with vector search, embeddings, and similarity metrics.
    - Strong understanding of REST API design and async execution.

    Preferred Skills
    - Experience with Docker, Linux systems, and FAISS IndexFlatL2 optimization.
    - Background in building LLM-assisted applications.

    Qualifications
    - Bachelor's or Master's degree in Computer Science or equivalent practical experience.
    """
    raw_jd_chunks = chunk_document(sample_jd, source="job_description", chunk_size=250, chunk_overlap=25)

    # User Details Chunks
    sample_user_details = """
    Target Role: Senior Backend Engineer
    Preferred Location: Remote / San Francisco, CA
    Years of Experience: 6 years
    Key Strengths: Scalable API development, vector retrieval, Python performance tuning
    """
    raw_user_chunks = chunk_document(sample_user_details, source="user_details", chunk_size=200, chunk_overlap=20)

    # 2. Store in KnowledgeStore
    print("\n[2] Populating KnowledgeStore with chunks...")
    store = KnowledgeStore()
    store.add_from_dicts(raw_resume_chunks)
    store.add_from_dicts(raw_jd_chunks)
    store.add_from_dicts(raw_user_chunks)

    num_chunks = len(store)
    print(f"    Number of chunks: {num_chunks}")
    print(f"    Chunk source breakdown: resume={len(raw_resume_chunks)}, job_description={len(raw_jd_chunks)}, user_details={len(raw_user_chunks)}")

    # 3. Load Embedding Model & Embed Chunks
    print(f"\n[3] Loading Embedding Model: {DEFAULT_MODEL_NAME}...")
    service = EmbeddingService.get_instance(DEFAULT_MODEL_NAME)
    model_name = service.model_name
    embedding_dim = service.get_dimension()

    print(f"    Embedding model name: {model_name}")
    print(f"    Embedding dimension: {embedding_dim}")

    print("\n[4] Generating and normalizing embeddings...")
    chunk_texts = store.get_texts()
    embeddings = service.encode(chunk_texts, normalize=True)

    num_vectors = embeddings.shape[0]
    first_vector_shape = embeddings[0].shape if num_vectors > 0 else (0,)

    # 4. Compute L2 norm of the first normalized vector
    first_vector_norm = float(np.linalg.norm(embeddings[0], ord=2)) if num_vectors > 0 else 0.0

    # 5. Output required test metrics
    print("\n" + "=" * 70)
    print("EMBEDDING LAYER VERIFICATION RESULTS")
    print("=" * 70)
    print(f"- number of chunks:                 {num_chunks}")
    print(f"- embedding model name:             {model_name}")
    print(f"- embedding dimension:              {embedding_dim}")
    print(f"- number of generated vectors:      {num_vectors}")
    print(f"- first vector shape:               {first_vector_shape}")
    print(f"- L2 norm of first vector:          {first_vector_norm:.6f}")

    # Check assertions
    assert num_chunks == num_vectors, f"Mismatch: {num_chunks} chunks vs {num_vectors} vectors"
    assert np.isclose(first_vector_norm, 1.0, atol=1e-5), f"L2 norm {first_vector_norm} is not approximately 1.0"
    
    # Verify all vectors have unit L2 norm
    all_norms = np.linalg.norm(embeddings, ord=2, axis=1)
    assert np.allclose(all_norms, 1.0, atol=1e-5), "Not all vectors have unit L2 norm!"

    print("\nVerification Passed:")
    print(f"  [x] number of chunks ({num_chunks}) == number of embeddings ({num_vectors})")
    print(f"  [x] L2 norm of all vectors == 1.0 (approx)")
    print(f"  [x] Normalized vectors ready for FAISS IndexFlatL2")
    print("=" * 70)


if __name__ == "__main__":
    main()
