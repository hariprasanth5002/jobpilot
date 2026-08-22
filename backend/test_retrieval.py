import json
import os
import numpy as np

from knowledge.embedding import EmbeddingService, DEFAULT_MODEL_NAME, normalize_embeddings
from knowledge.vector_store import VectorStore
from retrieval.retriever import Retriever, retrieve


def run_tests():
    print("=" * 75)
    print("JOBPILOT: RETRIEVAL LAYER TEST")
    print("=" * 75)

    storage_dir = "knowledge_base"
    index_file = os.path.join(storage_dir, "index.faiss")
    chunks_file = os.path.join(storage_dir, "chunks.json")

    # Load ground-truth chunks for verification
    with open(chunks_file, "r", encoding="utf-8") as f:
        ground_truth_chunks = json.load(f)

    # 1. Test Query Embedding Normalization Check
    print("\n[VERIFICATION] Verifying Query Embedding Normalization...")
    emb_service = EmbeddingService.get_instance(DEFAULT_MODEL_NAME)
    sample_emb = emb_service.encode(["Sample test query for normalization"], normalize=True)
    query_norm = float(np.linalg.norm(sample_emb[0], ord=2))
    print(f"    Sample query vector L2 norm: {query_norm:.6f}")
    assert np.isclose(query_norm, 1.0, atol=1e-5), f"Query norm {query_norm} is not 1.0"
    print("    [x] Query embedding normalization verified (||v||2 = 1.0)")

    # 2. Test Cases
    test_queries = [
        {
            "id": 1,
            "query": "What skills am I missing for this job?",
            "expected_intent": "SKILL_GAP",
            "expected_strategy": ["job_description", "resume"],
            "must_contain": None,
        },
        {
            "id": 2,
            "query": "What does AWS experience mean in this job description?",
            "expected_intent": "JD_EXPLANATION",
            "expected_strategy": ["job_description"],
            "must_contain": None,
        },
        {
            "id": 3,
            "query": "How should I prepare for this role?",
            "expected_intent": "PREPARATION",
            "expected_strategy": ["job_description", "resume", "user_details"],
            "must_contain": None,
        },
        {
            "id": 4,
            "query": "Give me possible interview questions for this role.",
            "expected_intent": "INTERVIEW_PREPARATION",
            "expected_strategy": ["job_description", "resume"],
            "must_contain": None,
        },
        {
            "id": 5,
            "query": "How should I explain my Agri Notifier project?",
            "expected_intent": "PROJECT_GUIDANCE",
            "expected_strategy": ["resume", "job_description"],
            "must_contain": "Agri",
            "must_contain_source": "resume",
        },
        {
            "id": 6,
            "query": "",
            "expected_intent": "GENERAL_JOB_QUESTION",
            "expected_strategy": ["resume", "job_description", "user_details"],
            "must_contain": None,
        },
        {
            "id": 7,
            "query": "   \n\t  ",
            "expected_intent": "GENERAL_JOB_QUESTION",
            "expected_strategy": ["resume", "job_description", "user_details"],
            "must_contain": None,
        },
    ]

    total_tests = len(test_queries)
    passed_tests = 0
    failed_tests = 0

    retriever = Retriever(storage_dir=storage_dir)

    for tc in test_queries:
        t_id = tc["id"]
        query = tc["query"]
        exp_intent = tc["expected_intent"]
        exp_strategy = tc["expected_strategy"]
        must_contain = tc.get("must_contain")
        must_contain_source = tc.get("must_contain_source")

        print("\n" + "-" * 75)
        print(f"QUERY: {repr(query)}")
        
        response = retriever.retrieve(query, top_k=5)
        res_intent = response.intent
        res_strategy = response.retrieval_strategy
        results = response.results

        print(f"INTENT: {res_intent}")
        print(f"STRATEGY: {res_strategy}")
        print("RETRIEVED CHUNKS:")

        if not results:
            print("  (No chunks retrieved - safe empty query handled)")
        else:
            for r in results:
                print(f"\nRank {r['rank']}")
                print(f"FAISS ID:  {r['faiss_id']}")
                print(f"Chunk ID:  {r['chunk_id']}")
                print(f"Distance:  {r['distance']:.6f}")
                print(f"Source:    {r['source']}")
                print(f"Section:   {r['section']}")
                safe_text = r['text'].encode('ascii', 'replace').decode('ascii')
                print(f"Text:      {safe_text}")

        # Assertions
        intent_ok = res_intent == exp_intent
        strategy_ok = res_strategy == exp_strategy

        # Verify mapping for every retrieved chunk
        mapping_ok = True
        for r in results:
            fid = r["faiss_id"]
            if fid < 0 or fid >= len(ground_truth_chunks):
                mapping_ok = False
                break
            gt = ground_truth_chunks[fid]
            if (
                gt["chunk_id"] != r["chunk_id"]
                or gt["source"] != r["source"]
                or gt["section"] != r["section"]
                or gt["text"] != r["text"]
            ):
                mapping_ok = False
                break

        # Check semantic content inclusion if required
        content_ok = True
        if must_contain and results:
            found = False
            for r in results:
                if must_contain.lower() in r["text"].lower():
                    if must_contain_source is None or r["source"] == must_contain_source:
                        found = True
                        break
            content_ok = found

        test_passed = intent_ok and strategy_ok and mapping_ok and content_ok

        if test_passed:
            passed_tests += 1
            print(f"\n-> TEST {t_id} RESULT: PASS")
        else:
            failed_tests += 1
            print(f"\n-> TEST {t_id} RESULT: FAIL (intent_ok={intent_ok}, strategy_ok={strategy_ok}, mapping_ok={mapping_ok}, content_ok={content_ok})")

    print("\n" + "=" * 75)
    print("RETRIEVAL LAYER TEST SUMMARY")
    print("=" * 75)
    print(f"Total Test Cases: {total_tests}")
    print(f"Passed:           {passed_tests}")
    print(f"Failed:           {failed_tests}")
    print("=" * 75)

    assert failed_tests == 0, f"{failed_tests} tests failed!"


if __name__ == "__main__":
    run_tests()
