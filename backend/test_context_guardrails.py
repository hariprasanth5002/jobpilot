import json
from retrieval.retriever import Retriever, retrieve
from generation.context_builder import build_context, format_llm_prompt_context, StructuredContext
from generation.guardrails import validate_context, GuardrailResult


def run_tests():
    print("=" * 75)
    print("JOBPILOT: CONTEXT BUILDER & GUARDRAILS TEST")
    print("=" * 75)

    retriever = Retriever(storage_dir="knowledge_base")

    total_tests = 4
    passed_tests = 0
    failed_tests = 0

    # ------------------------------------------------------------------------
    # TEST 1 — AWS GAP
    # ------------------------------------------------------------------------
    q1 = "What skills am I missing for this job?"
    print(f"\n[TEST 1] Testing AWS GAP: \"{q1}\"")
    retrieval_res1 = retriever.retrieve(q1, top_k=5)
    context1 = build_context(q1, retrieval_res1)
    guardrail1 = validate_context(context1)

    print(f"  Intent:                 {context1.intent}")
  # Check that JD contains AWS requirement and Resume has context
    jd_has_aws = any("aws" in c["text"].lower() for c in context1.job_description)
    resume_chunks_count = len(context1.resume)
    jd_chunks_count = len(context1.job_description)

    print(f"  Resume Chunks Count:    {resume_chunks_count}")
    print(f"  JD Chunks Count:        {jd_chunks_count}")
    print(f"  JD Contains AWS Req:    {jd_has_aws}")
    print(f"  Guardrail Allowed:      {guardrail1.allowed}")
    print(f"  Guardrail Warnings:     {guardrail1.warnings}")

    test1_pass = (
        guardrail1.allowed
        and jd_has_aws
        and jd_chunks_count > 0
    )
    if test1_pass:
        passed_tests += 1
        print("  -> TEST 1 RESULT: PASS")
    else:
        failed_tests += 1
        print("  -> TEST 1 RESULT: FAIL")

    # ------------------------------------------------------------------------
    # TEST 2 — PROJECT GUIDANCE
    # ------------------------------------------------------------------------
    q2 = "How should I explain my Agri Notifier project?"
    print(f"\n[TEST 2] Testing PROJECT GUIDANCE: \"{q2}\"")
    retrieval_res2 = retriever.retrieve(q2, top_k=5)
    context2 = build_context(q2, retrieval_res2)
    guardrail2 = validate_context(context2)

    resume_has_agri = any(
        "agri notifier" in c["text"].lower() and c["section"].lower() == "projects"
        for c in context2.resume
    )
    print(f"  Intent:                 {context2.intent}")
    print(f"  Resume Chunks Count:    {len(context2.resume)}")
    print(f"  Resume Has Agri Project:{resume_has_agri}")
    print(f"  Guardrail Allowed:      {guardrail2.allowed}")

    test2_pass = guardrail2.allowed and resume_has_agri
    if test2_pass:
        passed_tests += 1
        print("  -> TEST 2 RESULT: PASS")
    else:
        failed_tests += 1
        print("  -> TEST 2 RESULT: FAIL")

    # ------------------------------------------------------------------------
    # TEST 3 — JD EXPLANATION
    # ------------------------------------------------------------------------
    q3 = "What does AWS experience mean in this job description?"
    print(f"\n[TEST 3] Testing JD EXPLANATION: \"{q3}\"")
    retrieval_res3 = retriever.retrieve(q3, top_k=5)
    context3 = build_context(q3, retrieval_res3)
    guardrail3 = validate_context(context3)

    is_jd_dominated = len(context3.job_description) > len(context3.resume) and len(context3.job_description) > 0
    jd_has_aws = any("aws" in c["text"].lower() for c in context3.job_description)

    print(f"  Intent:                 {context3.intent}")
    print(f"  JD Chunks Count:        {len(context3.job_description)}")
    print(f"  Resume Chunks Count:    {len(context3.resume)}")
    print(f"  JD Contains AWS:        {jd_has_aws}")
    print(f"  Guardrail Allowed:      {guardrail3.allowed}")

    test3_pass = guardrail3.allowed and is_jd_dominated and jd_has_aws
    if test3_pass:
        passed_tests += 1
        print("  -> TEST 3 RESULT: PASS")
    else:
        failed_tests += 1
        print("  -> TEST 3 RESULT: FAIL")

    # ------------------------------------------------------------------------
    # TEST 4 — INSUFFICIENT CONTEXT
    # ------------------------------------------------------------------------
    q4 = "What is the secret passphrase for database deployment?"
    print(f"\n[TEST 4] Testing INSUFFICIENT CONTEXT: \"{q4}\"")
    # Simulate empty or insufficient retrieval result
    empty_retrieval = {
        "question": q4,
        "intent": "GENERAL_JOB_QUESTION",
        "retrieval_strategy": ["resume", "job_description", "user_details"],
        "results": [],
    }
    context4 = build_context(q4, empty_retrieval)
    guardrail4 = validate_context(context4)

    print(f"  Total Chunks:           {context4.total_chunks}")
    print(f"  Guardrail Allowed:      {guardrail4.allowed}")
    print(f"  Guardrail Warnings:     {guardrail4.warnings}")

    test4_pass = (
        not guardrail4.allowed
        and "Insufficient information in the retrieved context." in guardrail4.warnings
    )
    if test4_pass:
        passed_tests += 1
        print("  -> TEST 4 RESULT: PASS")
    else:
        failed_tests += 1
        print("  -> TEST 4 RESULT: FAIL")

    # ------------------------------------------------------------------------
    # Print Sample LLM Prompt Context
    # ------------------------------------------------------------------------
    print("\n" + "=" * 75)
    print("EXAMPLE GENERATED LLM PROMPT CONTEXT (FROM TEST 1)")
    print("=" * 75)
    safe_prompt = guardrail1.prompt_context.encode('ascii', 'replace').decode('ascii')
    print(safe_prompt)
    print("=" * 75)

    print("\n" + "=" * 75)
    print("CONTEXT BUILDER & GUARDRAILS TEST SUMMARY")
    print("=" * 75)
    print(f"Total Test Cases: {total_tests}")
    print(f"Passed:           {passed_tests}")
    print(f"Failed:           {failed_tests}")
    print("=" * 75)

    assert failed_tests == 0, f"{failed_tests} tests failed!"


if __name__ == "__main__":
    run_tests()
