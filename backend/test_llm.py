import json
import os
import sys

from retrieval.retriever import Retriever
from generation.context_builder import build_context
from generation.guardrails import validate_context
from generation.llm import OllamaClient, generate_answer


def main():
    print("=" * 80)
    print("JOBPILOT: LLM GENERATION LAYER TEST (OLLAMA)")
    print("=" * 80)

    # 1. PRE-FLIGHT OLLAMA TEST
    print("\n[1] Running Pre-Flight Ollama Connectivity & Model Check...")
    client = OllamaClient()
    try:
        health = client.check_health()
        print(f"    Ollama Status:       {health['status'].upper()}")
        print(f"    Ollama Host:         {health['host']}")
        print(f"    Available Models:    {health['available_models']}")
        print(f"    Configured Model:    {health['configured_model']}")
        print(f"    Model Ready:         {health['model_ready']}")

        if not health["available_models"]:
            print("\n[!] FATAL: No Ollama models found locally.")
            sys.exit(1)
        if not health["model_ready"]:
            print(f"\n[!] Selected model '{client.model}' not in available models. Switching...")
            client.model = health["available_models"][0]
            print(f"    Active Model set to: {client.model}")
    except Exception as e:
        print(f"\n[!] FATAL: Pre-flight check failed to connect to Ollama: {e}")
        sys.exit(1)

    # 2. Setup Retriever
    retriever = Retriever(storage_dir="knowledge_base")

    test_cases = [
        {
            "id": 1,
            "title": "SKILL GAP ANALYSIS",
            "question": "What skills am I missing for this job?",
            "expected_intent": "SKILL_GAP",
            "is_sufficient": True,
        },
        {
            "id": 2,
            "title": "JOB DESCRIPTION EXPLANATION",
            "question": "What does AWS experience mean in this job description?",
            "expected_intent": "JD_EXPLANATION",
            "is_sufficient": True,
        },
        {
            "id": 3,
            "title": "PROJECT GUIDANCE",
            "question": "How should I explain my Agri Notifier project?",
            "expected_intent": "PROJECT_GUIDANCE",
            "is_sufficient": True,
        },
        {
            "id": 4,
            "title": "ROLE PREPARATION",
            "question": "How should I prepare for this role?",
            "expected_intent": "PREPARATION",
            "is_sufficient": True,
        },
        {
            "id": 5,
            "title": "INSUFFICIENT CONTEXT / GUARDRAIL INTERCEPTION",
            "question": "What is the secret passphrase for database deployment?",
            "expected_intent": "GENERAL_JOB_QUESTION",
            "is_sufficient": False,
            "force_empty_retrieval": True,
        },
    ]

    total_tests = len(test_cases)
    passed_tests = 0
    failed_tests = 0

    for tc in test_cases:
        t_id = tc["id"]
        title = tc["title"]
        q = tc["question"]
        exp_intent = tc["expected_intent"]
        is_suff = tc["is_sufficient"]
        force_empty = tc.get("force_empty_retrieval", False)

        print("\n" + "=" * 80)
        print(f"TEST {t_id}: {title}")
        print(f"QUESTION: {q}")
        print("=" * 80)

        # Retrieval
        if force_empty:
            retrieval_res = {
                "question": q,
                "intent": exp_intent,
                "retrieval_strategy": ["resume", "job_description", "user_details"],
                "results": [],
            }
        else:
            retrieval_res = retriever.retrieve(q, top_k=5)

        # Context Building
        context = build_context(q, retrieval_res)

        # Guardrail Validation
        guardrail_res = validate_context(context)

        # Generation
        gen_result = generate_answer(
            question=q,
            intent=context.intent,
            validated_guardrail_result=guardrail_res,
            client=client,
        )

        print(f"\nINTENT: {gen_result['intent']}")
        print(f"GUARDRAIL ALLOWED: {gen_result['allowed']}")
        print(f"CALLED OLLAMA:     {gen_result['called_llm']}")
        if gen_result["warnings"]:
            print(f"WARNINGS:          {gen_result['warnings']}")

        print("\nANSWER:\n")
        print(gen_result["answer"])
        print("\n" + "-" * 80)

        # Verification Assertions
        if not is_suff:
            # Must NOT call Ollama, must return safe message
            test_passed = (
                not gen_result["allowed"]
                and not gen_result["called_llm"]
                and "sufficient information" in gen_result["answer"].lower()
            )
        else:
            # Must call Ollama and return non-empty answer matching intent
            test_passed = (
                gen_result["allowed"]
                and gen_result["called_llm"]
                and len(gen_result["answer"]) > 50
                and gen_result["intent"] == exp_intent
            )

        if test_passed:
            passed_tests += 1
            print(f"-> TEST {t_id} RESULT: PASS")
        else:
            failed_tests += 1
            print(f"-> TEST {t_id} RESULT: FAIL")

    print("\n" + "=" * 80)
    print("LLM GENERATION LAYER TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests:  {total_tests}")
    print(f"Passed Tests: {passed_tests}")
    print(f"Failed Tests: {failed_tests}")
    print(f"Ollama Model: {client.model}")
    print("=" * 80)

    assert failed_tests == 0, f"{failed_tests} tests failed!"


if __name__ == "__main__":
    main()
