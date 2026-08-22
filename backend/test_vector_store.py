import os
import numpy as np

from processing.document_loader import extract_pdf_text
from processing.cleaner import clean_text
from processing.section_detector import detect_sections
from processing.chunker import chunk_sections, chunk_document
from knowledge.knowledge_store import KnowledgeStore
from knowledge.embedding import EmbeddingService, DEFAULT_MODEL_NAME
from knowledge.vector_store import VectorStore, build_index, load_index


def main():
    print("=" * 70)
    print("JOBPILOT: FAISS VECTOR STORE LAYER TEST")
    print("=" * 70)

    # Step A: Load chunks produced by processing pipeline
    print("\n[A] Producing chunks via processing pipeline...")
    sample_pdf_path = "sample_resume.pdf"
    from test_processing import create_sample_resume_pdf
    create_sample_resume_pdf(sample_pdf_path)

    raw_pdf_text = extract_pdf_text(sample_pdf_path)
    cleaned_pdf_text = clean_text(raw_pdf_text)
    resume_sections = detect_sections(cleaned_pdf_text)
    raw_resume_chunks = chunk_sections(resume_sections, source="resume", chunk_size=300, chunk_overlap=30)

    sample_jd = """
    About the Role
    We are looking for a Senior AI & Backend Engineer to build high-performance retrieval pipelines and integrate local LLMs for structured query processing.

    Responsibilities
    - Design and develop scalable FastAPI services for document parsing and FAISS vector indexing.
    - Implement robust section detection and chunking algorithms.
    - Deploy cloud services on AWS and integrate Ollama LLMs with strict guardrails and prompt templates.

    Requirements
    - 4+ years of professional backend engineering experience in Python.
    - Hands-on experience with AWS cloud services, vector search, embeddings, and similarity metrics.
    - Strong understanding of REST API design and async execution.

    Preferred Skills
    - Experience with AWS EC2/S3, Docker, Linux systems, and FAISS IndexFlatL2 optimization.
    - Background in building LLM-assisted applications.

    Qualifications
    - Bachelor's or Master's degree in Computer Science or equivalent practical experience.
    """
    raw_jd_chunks = chunk_document(sample_jd, source="job_description", chunk_size=250, chunk_overlap=25)

    sample_user_details = """
    Target Role: Senior Backend Engineer
    Preferred Location: Remote / San Francisco, CA
    Years of Experience: 6 years
    Key Strengths: Scalable API development, vector retrieval, Python performance tuning
    """
    raw_user_chunks = chunk_document(sample_user_details, source="user_details", chunk_size=200, chunk_overlap=20)

    # Store in KnowledgeStore
    store = KnowledgeStore()
    store.add_from_dicts(raw_resume_chunks)
    store.add_from_dicts(raw_jd_chunks)
    store.add_from_dicts(raw_user_chunks)

    # Step B: Generate normalized embeddings
    print("\n[B] Generating normalized embeddings...")
    embedding_service = EmbeddingService.get_instance(DEFAULT_MODEL_NAME)
    chunk_texts = store.get_texts()
    embeddings = embedding_service.encode(chunk_texts, normalize=True)

    # Step C: Build FAISS IndexFlatL2
    print("\n[C] Building FAISS IndexFlatL2...")
    v_store = VectorStore()
    v_store.build_index(embeddings, store)

    # Step D: Print Index Information
    print("\n[D] FAISS Index Details:")
    print(f"    Number of vectors:   {v_store.total_vectors}")
    print(f"    Embedding dimension: {v_store.dimension}")
    print(f"    FAISS index type:    {v_store.index_type}")

    # Step E: Save Index and Metadata
    storage_dir = "knowledge_base"
    print(f"\n[E] Saving index and chunk metadata to '{storage_dir}/'...")
    index_path, chunks_path = v_store.save_index(storage_dir=storage_dir)
    print(f"    Saved FAISS index:    {os.path.abspath(index_path)}")
    print(f"    Saved chunk metadata: {os.path.abspath(chunks_path)}")

    # Step F: Load Saved FAISS Index
    print(f"\n[F] Loading saved FAISS index from disk...")
    loaded_store = VectorStore()
    loaded_store.load_index(storage_dir=storage_dir)
    print(f"    Loaded {loaded_store.total_vectors} vectors with dimension {loaded_store.dimension}.")

    # Step G: Test Query & Embedding
    query = "What experience do I have with Python, backend development, and FAISS?"
    print(f"\n[G] Embedding and normalizing test query: \"{query}\"")
    query_vector = embedding_service.encode([query], normalize=True)

    # Step H: Search FAISS Index
    k = 5
    print(f"\n[H] Searching FAISS index with k={k}...")
    results = loaded_store.search_with_metadata(query_vector, k=k)

    # Step I: Print Results in Required Format
    print("\n[I] Search Results:")
    print("=" * 70)
    for res in results:
        print(f"Rank:        {res['rank']}")
        print(f"FAISS ID:    {res['faiss_id']}")
        print(f"L2 distance: {res['l2_distance']:.6f}")
        print(f"Chunk ID:    {res['chunk_id']}")
        print(f"Source:      {res['source']}")
        print(f"Section:     {res['section']}")
        print(f"Text:        {res['text']}")
        print("-" * 70)

    # Step J: Verification of 1:1 Mapping
    print("\n[J] Verifying FAISS ID -> Chunk Metadata Mapping...")
    for res in results:
        faiss_id = res["faiss_id"]
        direct_chunk = loaded_store.get_chunk(faiss_id)
        assert direct_chunk is not None, f"Chunk for FAISS ID {faiss_id} not found!"
        assert direct_chunk["chunk_id"] == res["chunk_id"], "Chunk ID mismatch!"
        assert direct_chunk["text"] == res["text"], "Text content mismatch!"
        assert direct_chunk["source"] == res["source"], "Source mismatch!"
        assert direct_chunk["section"] == res["section"], "Section mismatch!"

    print(f"    [x] All {len(results)} search results verified against chunks.json metadata.")
    print("    [x] FAISS ID precisely matches chunk position and metadata.")

    print("\n" + "=" * 70)
    print("FAISS VECTOR STORE TEST COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
