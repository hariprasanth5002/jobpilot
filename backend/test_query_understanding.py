from retrieval.query_understanding import (
    Intent,
    INTENT_RETRIEVAL_STRATEGIES,
    understand_query,
)


def run_tests():
    print("=" * 75)
    print("JOBPILOT: QUERY UNDERSTANDING LAYER TEST")
    print("=" * 75)

    test_cases = [
        # 1. Skill Gap
        {
            "query": "What skills am I missing for this job?",
            "expected_intent": Intent.SKILL_GAP.value,
            "expected_strategy": ["job_description", "resume"],
            "description": "Missing skills question",
        },
        # 2. JD Explanation
        {
            "query": "What does AWS experience mean in this job description?",
            "expected_intent": Intent.JD_EXPLANATION.value,
            "expected_strategy": ["job_description"],
            "description": "JD terminology explanation",
        },
        # 3. Preparation
        {
            "query": "How should I prepare for this role?",
            "expected_intent": Intent.PREPARATION.value,
            "expected_strategy": ["job_description", "resume", "user_details"],
            "description": "Role preparation question",
        },
        # 4. Interview Preparation
        {
            "query": "Give me possible interview questions for this role.",
            "expected_intent": Intent.INTERVIEW_PREPARATION.value,
            "expected_strategy": ["job_description", "resume"],
            "description": "Interview questions request",
        },
        # 5. Project Guidance
        {
            "query": "How should I explain my Agri Notifier project?",
            "expected_intent": Intent.PROJECT_GUIDANCE.value,
            "expected_strategy": ["resume", "job_description"],
            "description": "Project explanation guidance",
        },
        # 6. Resume-JD Match
        {
            "query": "How well does my resume match this job?",
            "expected_intent": Intent.RESUME_JD_MATCH.value,
            "expected_strategy": ["resume", "job_description"],
            "description": "Resume & JD match comparison",
        },
        # 7. General Job Question
        {
            "query": "What is my target role?",
            "expected_intent": Intent.GENERAL_JOB_QUESTION.value,
            "expected_strategy": ["resume", "job_description", "user_details"],
            "description": "General profile query",
        },
        # 8. Skill improvement before interview
        {
            "query": "What skills do I need to improve before the interview?",
            "expected_intent": Intent.SKILL_GAP.value,
            "expected_strategy": ["job_description", "resume"],
            "description": "Skills to improve before interview",
        },
        # 9. Case Insensitivity (UPPERCASE)
        {
            "query": "WHAT SKILLS AM I MISSING?",
            "expected_intent": Intent.SKILL_GAP.value,
            "expected_strategy": ["job_description", "resume"],
            "description": "Case insensitivity test (ALL CAPS)",
        },
        # 10. Case Insensitivity (Mixed Case)
        {
            "query": "hOw ShOuLd I eXpLaIn My AgRi NoTiFiEr PrOjEcT?",
            "expected_intent": Intent.PROJECT_GUIDANCE.value,
            "expected_strategy": ["resume", "job_description"],
            "description": "Case insensitivity test (mIxEd cAsE)",
        },
        # 11. Empty string handling
        {
            "query": "",
            "expected_intent": Intent.GENERAL_JOB_QUESTION.value,
            "expected_strategy": ["resume", "job_description", "user_details"],
            "description": "Empty string safe fallback",
        },
        # 12. Whitespace string handling
        {
            "query": "   \n\t  ",
            "expected_intent": Intent.GENERAL_JOB_QUESTION.value,
            "expected_strategy": ["resume", "job_description", "user_details"],
            "description": "Whitespace only safe fallback",
        },
        # 13. Additional variation: JD Explanation
        {
            "query": "Explain the responsibilities in this job description.",
            "expected_intent": Intent.JD_EXPLANATION.value,
            "expected_strategy": ["job_description"],
            "description": "JD responsibilities explanation",
        },
        # 14. Additional variation: Project Guidance
        {
            "query": "What project should I highlight?",
            "expected_intent": Intent.PROJECT_GUIDANCE.value,
            "expected_strategy": ["resume", "job_description"],
            "description": "Project highlighting question",
        },
    ]

    total_tests = len(test_cases)
    passed_tests = 0
    failed_tests = 0

    print(f"\nRunning {total_tests} test cases...\n")

    for idx, tc in enumerate(test_cases, start=1):
        query = tc["query"]
        expected_intent = tc["expected_intent"]
        expected_strategy = tc["expected_strategy"]
        desc = tc["description"]

        result = understand_query(query)
        intent_match = result.intent == expected_intent
        strategy_match = result.retrieval_strategy == expected_strategy

        if intent_match and strategy_match:
            passed_tests += 1
            status = "PASS"
        else:
            failed_tests += 1
            status = "FAIL"

        print(f"[{status}] Test {idx:02d}: {desc}")
        print(f"       Query:              \"{query}\"")
        print(f"       Identified Intent:  {result.intent} (Expected: {expected_intent})")
        print(f"       Strategy:           {result.retrieval_strategy}")
        if status == "FAIL":
            print(f"       ERROR: Strategy Expected: {expected_strategy}")
        print("-" * 75)

    print("\n" + "=" * 75)
    print("QUERY UNDERSTANDING TEST SUMMARY")
    print("=" * 75)
    print(f"Total Test Cases:  {total_tests}")
    print(f"Passed:            {passed_tests}")
    print(f"Failed:            {failed_tests}")

    assert failed_tests == 0, f"{failed_tests} tests failed!"
    print("\nALL QUERY UNDERSTANDING TESTS PASSED!")
    print("=" * 75)


if __name__ == "__main__":
    run_tests()
